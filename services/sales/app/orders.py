"""OrderService port — quote/order workflows and auto-invoice generation.

Preserved quirks, deliberately:

* Numbering, totals and validation run here (they ran in the monolith's
  service + route layer) against this service's own database.
* The monolith's ``_generate_invoice`` crashed on an undefined ``OrderModel``
  *after* creating the invoice but *before* linking it or deducting stock, so
  in production the link was never written and stock moved only when the
  invoice was later marked paid. The linkage is repaired here (clear intent);
  deduction still happens **only** through the invoice-paid events, which
  keeps today's observable stock behaviour (no double deduction).
* Cross-service product lookups are synchronous; stock effects are events.
"""

import logging
from datetime import datetime, timezone

from si_common.events import activity, emit_event
from si_common.ids import oid, tenant_filter
from si_common.validators import (collect_errors, validate_numeric,
                                  validate_required)

from . import catalog, repos

logger = logging.getLogger(__name__)


def _emit(event_type, *, identity, act=None, payload=None):
    return emit_event(repos.orders.db, event_type, source='sales',
                      company_id=identity.company_id,
                      actor_user_id=identity.user_id,
                      activity=act, payload=payload)


def _scope(identity):
    return tenant_filter(identity.company_id)


# --- validation -----------------------------------------------------------

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
        except (ValueError, TypeError):
            errors.append(f'Item {idx + 1}: Quantity must be an integer.')

    if data.get('discount_percent'):
        err = validate_numeric(data.get('discount_percent'), 'Discount', 0, 100)
        if err:
            errors.append(err)

    return collect_errors(errors)


# --- totals / numbering ---------------------------------------------------

def _totals(items, discount_percent, tax_percent):
    subtotal = sum(it['total'] for it in items)
    discount_pct = float(discount_percent or 0)
    discount_amt = round(subtotal * (discount_pct / 100), 2)
    after_discount = subtotal - discount_amt
    tax_pct = float(tax_percent if tax_percent is not None else 10)
    tax_amount = round(after_discount * (tax_pct / 100), 2)
    total = round(after_discount + tax_amount, 2)
    return round(subtotal, 2), discount_pct, discount_amt, tax_pct, tax_amount, total


def _build_items(raw_items, identity):
    items = []
    for it in raw_items:
        product = catalog.find_by_sku(it['sku'], identity)
        qty = int(it['quantity'])
        up = float(it.get('unit_price', product['price']))
        line_total = round(qty * up, 2)
        items.append({
            'sku': it['sku'],
            'name': it.get('name', product['name']),
            'description': it.get('description', product.get('description', '')),
            'quantity': qty,
            'unit_price': up,
            'total': line_total,
        })
    return items


def _next_number(repo, identity, prefix, width=2):
    count = repo.count(_scope(identity))
    return f"{prefix}{datetime.now().strftime('%d%m%y')}-{count + 1:0{width}d}"


# --- lifecycle ------------------------------------------------------------

def create(data, identity):
    items = _build_items(data['items'], identity)
    subtotal, disc_pct, disc_amt, tax_pct, tax_amt, total = _totals(
        items, data.get('discount_percent'), data.get('tax_percent', 10))

    order_data = {
        'order_number': _next_number(repos.orders, identity, 'O'),
        'customer_name': data['customer_name'].strip(),
        'contact_name': (data.get('contact_name') or '').strip(),
        'contact_email': (data.get('contact_email') or '').strip(),
        'customer_address': (data.get('customer_address') or '').strip(),
        'items': items,
        'subtotal': subtotal,
        'discount_percent': disc_pct,
        'discount_amount': disc_amt,
        'tax_percent': tax_pct,
        'tax_amount': tax_amt,
        'total': total,
        'status': data.get('status', 'pending'),
        'notes': (data.get('notes') or '').strip(),
        'company_id': oid(identity.company_id),
        'created_by': oid(identity.user_id),
        'generated_invoice_id': None,
        'generated_invoice_number': None,
    }

    order_id = repos.orders.create(order_data)
    logger.info('Customer Order created: %s (id=%s, company=%s, total=%.2f, by=%s)',
                order_data['order_number'], order_id, identity.company_id,
                total, identity.user_id)

    if order_data['status'] == 'confirmed':
        _generate_invoice(order_id, order_data, identity)

    _emit('sales.order.created', identity=identity,
          act=activity('order', order_id, order_data['order_number'], 'created'))
    return order_id, order_data['order_number']


def update(order_id, data, identity):
    order = repos.orders.find_by_id(order_id, _scope(identity))
    if not order:
        return None

    old_status = order.get('status')
    new_status = data.get('status', old_status)
    update_data = {'status': new_status}

    if data.get('notes'):
        update_data['notes'] = data['notes'].strip()
    if data.get('customer_name'):
        update_data['customer_name'] = data['customer_name'].strip()
    if 'contact_name' in data:
        update_data['contact_name'] = (data.get('contact_name') or '').strip()
    if 'contact_email' in data:
        update_data['contact_email'] = (data.get('contact_email') or '').strip()

    repos.orders.update(order_id, update_data)
    logger.info('Customer Order updated: %s (id=%s, status=%s->%s, by=%s)',
                order.get('order_number'), order_id, old_status, new_status,
                identity.user_id)

    if (new_status == 'confirmed' and old_status != 'confirmed'
            and not order.get('generated_invoice_id')):
        _generate_invoice(order_id, {**order, **update_data}, identity)

    if 'status' in data:
        _emit('sales.order.status_changed', identity=identity,
              act=activity('order', order_id, order.get('order_number', ''),
                           'status_changed',
                           changes={'from': old_status, 'to': new_status}),
              payload={'order_number': order.get('order_number', ''),
                       'from': old_status, 'to': new_status})
    return True


def _generate_invoice(order_id, order_data, identity):
    """Auto-create the invoice for a confirmed order and link it back."""
    try:
        now = datetime.now(timezone.utc)
        invoice_number = _next_number(repos.invoices, identity, 'I')
        doc = {
            'invoice_number': invoice_number,
            'customer_name': order_data['customer_name'],
            'contact_name': order_data.get('contact_name', ''),
            'contact_email': order_data.get('contact_email', ''),
            'customer_address': order_data.get('customer_address', ''),
            'invoice_date': now,
            'due_date': now,
            'items': order_data['items'],
            'subtotal': float(order_data.get('subtotal', 0)),
            'discount_percent': float(order_data.get('discount_percent', 0)),
            'discount_amount': float(order_data.get('discount_amount', 0)),
            'tax_percent': float(order_data.get('tax_percent', 10)),
            'tax_amount': float(order_data.get('tax_amount', 0)),
            'total': float(order_data.get('total', 0)),
            'status': 'sent',
            'notes': f"Auto-generated from Order {order_data.get('order_number')}",
            'company_id': oid(identity.company_id),
            'created_by': oid(identity.user_id),
            'from_order_id': oid(order_id),
            'from_order_number': order_data.get('order_number'),
        }
        invoice_id = repos.invoices.create(doc)

        repos.orders.update(order_id, {
            'generated_invoice_id': oid(invoice_id),
            'generated_invoice_number': invoice_number,
        })

        # Domain event, no activity row: the monolith never logged these
        # auto-generated invoices in the activity feed.
        _emit('sales.invoice.created', identity=identity,
              payload={'invoice_number': invoice_number,
                       'items': order_data['items'], 'status': 'sent'})

        logger.info('Invoice %s auto-generated from Order %s',
                    invoice_number, order_data.get('order_number'))
    except Exception:
        logger.exception('Failed to generate invoice from order %s', order_id)


# --- reads ----------------------------------------------------------------

def get_by_id(order_id, identity):
    order = repos.orders.find_by_id(order_id, _scope(identity))
    from .serialize import order_out
    return order_out(order)


def list(page, per_page, filters, identity):
    from .serialize import order_out
    from si_common.tenancy import scoped
    docs, total = repos.orders.find_all(page, per_page, scoped(identity, filters))
    return [order_out(d) for d in docs], total


def get_recent(limit=5, identity=None, filters=None):
    from .serialize import order_out
    from si_common.tenancy import scoped
    docs = repos.orders.recent(limit, scoped(identity, filters))
    return [order_out(d) for d in docs]


def get_counts(identity):
    from si_common.tenancy import scoped
    filters = scoped(identity)
    total = repos.orders.count(filters)
    return {
        'total': total,
        'pending': repos.orders.count({**filters, 'status': 'pending'}),
        'confirmed': repos.orders.count({**filters, 'status': 'confirmed'}),
        'shipped': repos.orders.count({**filters, 'status': 'shipped'}),
        'delivered': repos.orders.count({**filters, 'status': 'delivered'}),
        'cancelled': repos.orders.count({**filters, 'status': 'cancelled'}),
    }
