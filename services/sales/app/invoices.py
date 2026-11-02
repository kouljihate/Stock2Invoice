"""InvoiceService port — creation, status workflow and sales totals.

Deduction semantics: the monolith deducted stock synchronously when an
invoice was created as ``paid`` or transitioned to ``paid`` (best-effort,
logging on failure). Those two transitions are now single domain events that
inventory-service consumes idempotently; everything else about validation
and totals is synchronous and byte-for-byte identical.
"""

import logging
from datetime import datetime, timedelta, timezone

from si_common.events import activity, emit_event
from si_common.ids import oid, tenant_filter
from si_common.validators import (collect_errors, validate_numeric,
                                  validate_required)

from . import catalog, repos

logger = logging.getLogger(__name__)


def _emit(event_type, *, identity, act=None, payload=None):
    return emit_event(repos.invoices.db, event_type, source='sales',
                      company_id=identity.company_id,
                      actor_user_id=identity.user_id,
                      activity=act, payload=payload)


def _scope(identity):
    return tenant_filter(identity.company_id)


def validate(data, identity):
    errors = []
    errors.append(validate_required(data.get('customer_name'), 'Customer name'))

    items = data.get('items', [])
    if not items or not isinstance(items, list):
        errors.append('At least one line item is required.')
        return collect_errors(errors)

    for idx, item in enumerate(items):
        sku = (item.get('sku') or '').strip()
        if not sku:
            errors.append(f'Item {idx + 1}: SKU is required.')
            continue
        product = catalog.find_by_sku(sku, identity)
        if not product:
            errors.append(f'Item {idx + 1}: Product with SKU "{sku}" not found.')
            continue
        qty = item.get('quantity', 0)
        try:
            qty = int(qty)
            if qty <= 0:
                errors.append(f'Item {idx + 1}: Quantity must be positive.')
            elif product['quantity'] < qty and data.get('status') == 'paid':
                errors.append(f'Item {idx + 1}: Insufficient stock for "{sku}" '
                              f'(available: {product["quantity"]}).')
        except (ValueError, TypeError):
            errors.append(f'Item {idx + 1}: Quantity must be an integer.')

    if data.get('discount_percent'):
        err = validate_numeric(data.get('discount_percent'), 'Discount', 0, 100)
        if err:
            errors.append(err)

    return collect_errors(errors)


def _build_items(raw_items, identity):
    items = []
    for it in raw_items:
        product = catalog.find_by_sku(it['sku'], identity)
        qty = int(it['quantity'])
        up = float(it.get('unit_price', product['price']))
        items.append({
            'sku': it['sku'],
            'name': it.get('name', product['name']),
            'description': it.get('description', product.get('description', '')),
            'quantity': qty,
            'unit_price': up,
            'total': round(qty * up, 2),
            'pack_size': it.get('pack_size', ''),
            'package_type': it.get('package_type', ''),
            'pack_size_unit': it.get('pack_size_unit', ''),
        })
    return items


def create(data, identity):
    items = _build_items(data['items'], identity)
    subtotal = sum(it['total'] for it in items)

    discount_pct = float(data.get('discount_percent', 0))
    discount_amt = round(subtotal * (discount_pct / 100), 2)
    after_discount = subtotal - discount_amt
    tax_pct = float(data.get('tax_percent', 10))
    tax_amt = round(after_discount * (tax_pct / 100), 2)
    total = round(after_discount + tax_amt, 2)

    count = repos.invoices.count(_scope(identity))
    invoice_number = f"I{datetime.now().strftime('%d%m%y')}-{count + 1:02d}"
    now = datetime.now(timezone.utc)

    invoice_data = {
        'invoice_number': invoice_number,
        'customer_name': data['customer_name'].strip(),
        'contact_name': (data.get('contact_name') or '').strip(),
        'contact_email': (data.get('contact_email') or '').strip(),
        'customer_address': (data.get('customer_address') or '').strip(),
        'customer_city': (data.get('customer_city') or '').strip(),
        'customer_country': (data.get('customer_country') or '').strip(),
        'attention_to': (data.get('attention_to') or '').strip(),
        'delivery_time': (data.get('delivery_time') or '').strip(),
        'invoice_date': now,
        'due_date': data.get('due_date') or now,
        'items': items,
        'subtotal': round(subtotal, 2),
        'discount_percent': discount_pct,
        'discount_amount': discount_amt,
        'tax_percent': tax_pct,
        'tax_amount': tax_amt,
        'total': total,
        'status': data.get('status', 'draft'),
        'notes': (data.get('notes') or '').strip(),
        'company_id': oid(identity.company_id),
        'created_by': oid(identity.user_id),
    }

    invoice_id = repos.invoices.create(invoice_data)
    logger.info('Invoice %s created: %s (id=%s, company=%s, total=%.2f, by=%s)',
                invoice_number, invoice_data['customer_name'], invoice_id,
                identity.company_id, total, identity.user_id)

    # One event serves both consumers: workers writes the activity row the
    # routes used to write, inventory deducts when status == 'paid'.
    _emit('sales.invoice.created', identity=identity,
          act=activity('invoice', invoice_id, invoice_number, 'created'),
          payload={'invoice_number': invoice_number, 'items': items,
                   'status': invoice_data['status']})

    return invoice_id, invoice_number


def update(invoice_id, data, identity):
    inv = repos.invoices.find_by_id(invoice_id, _scope(identity))
    if not inv:
        return None

    old_status = inv.get('status')
    update_data = {}

    if data.get('status') and data['status'] != old_status:
        update_data['status'] = data['status']

    if data.get('notes'):
        update_data['notes'] = data['notes'].strip()
    if data.get('customer_name'):
        update_data['customer_name'] = data['customer_name'].strip()
    if 'contact_name' in data:
        update_data['contact_name'] = (data.get('contact_name') or '').strip()
    if 'contact_email' in data:
        update_data['contact_email'] = (data.get('contact_email') or '').strip()
    if 'attention_to' in data:
        update_data['attention_to'] = (data.get('attention_to') or '').strip()
    if 'delivery_time' in data:
        update_data['delivery_time'] = (data.get('delivery_time') or '').strip()
    if data.get('invoice_date'):
        update_data['invoice_date'] = datetime.fromisoformat(data['invoice_date'])
    if data.get('due_date'):
        update_data['due_date'] = datetime.fromisoformat(data['due_date'])
    if 'items' in data and isinstance(data['items'], list):
        update_data['items'] = data['items']

    if update_data:
        repos.invoices.update(invoice_id, update_data, touch_updated=False)
        logger.info('Invoice updated: %s (id=%s, by=%s)',
                    inv.get('invoice_number'), invoice_id, identity.user_id)

    if 'status' in data:
        new_status = data['status']
        _emit('sales.invoice.status_changed', identity=identity,
              act=activity('invoice', invoice_id, inv.get('invoice_number', ''),
                           'status_changed',
                           changes={'from': old_status, 'to': new_status}),
              payload={'invoice_number': inv.get('invoice_number', ''),
                       'items': inv.get('items', []),
                       'from': old_status, 'to': new_status})

    return True


# --- reads ----------------------------------------------------------------

def get_by_id(invoice_id, identity):
    from .serialize import invoice_out
    return invoice_out(repos.invoices.find_by_id(invoice_id, _scope(identity)))


def list(page, per_page, filters, identity):
    from .serialize import invoice_out
    from si_common.tenancy import scoped
    docs, total = repos.invoices.find_all(page, per_page, scoped(identity, filters))
    return [invoice_out(d) for d in docs], total


def get_recent(limit=5, identity=None):
    from .serialize import invoice_out
    from si_common.tenancy import scoped
    docs = repos.invoices.recent(limit, scoped(identity))
    return [invoice_out(d) for d in docs]


def get_counts(identity):
    from si_common.tenancy import scoped
    filters = scoped(identity)
    return {
        'total': repos.invoices.count(filters),
        'draft': repos.invoices.count({**filters, 'status': 'draft'}),
        'sent': repos.invoices.count({**filters, 'status': 'sent'}),
        'paid': repos.invoices.count({**filters, 'status': 'paid'}),
        'cancelled': repos.invoices.count({**filters, 'status': 'cancelled'}),
    }


def _sales_total(identity, start):
    match = {'status': 'paid', 'created_at': {'$gte': start}}
    match.update(_scope(identity))
    rows = repos.invoices.aggregate([
        {'$match': match},
        {'$group': {'_id': None, 'total': {'$sum': '$total'}}},
    ])
    return round(rows[0]['total'], 2) if rows else 0.0


def get_month_sales(identity):
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return _sales_total(identity, start)


def get_year_sales(identity):
    now = datetime.now(timezone.utc)
    start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return _sales_total(identity, start)
