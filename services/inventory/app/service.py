"""StockService port: validation, product lifecycle, stock deduction.

Behaviour preserved from the monolith, including the deliberate nuances:
validation errors are strings, deduction is best-effort (insufficient stock
logs and returns False), and stock *movement documents* are never written —
the original only ever recorded movement **activity** through the event log.
"""

import logging
import re

from si_common.events import activity, emit_event
from si_common.ids import tenant_filter
from si_common.validators import (collect_errors, validate_integer,
                                  validate_numeric, validate_required,
                                  validate_string_length)

from . import repos

logger = logging.getLogger(__name__)


def _emit(event_type, *, company_id, user_id, act, payload=None):
    return emit_event(repos.products.db, event_type, source='inventory',
                      company_id=company_id, actor_user_id=user_id,
                      activity=act, payload=payload)


# --- validation -----------------------------------------------------------

def validate(data, company_id, is_update=False):
    errors = []
    errors.append(validate_required(data.get('name'), 'Product name'))
    errors.append(validate_string_length(data.get('name'), 'Product name', 1, 200))
    errors.append(validate_required(data.get('sku'), 'SKU'))
    errors.append(validate_string_length(data.get('sku'), 'SKU', 1, 100))
    errors.append(validate_integer(data.get('quantity'), 'Quantity', 0))
    errors.append(validate_numeric(data.get('price'), 'Price', 0))
    if data.get('purchase_price') is not None:
        errors.append(validate_numeric(data.get('purchase_price'), 'Purchase price', 0))
    if data.get('quantity_min') is not None:
        errors.append(validate_integer(data.get('quantity_min'), 'Min quantity', 0))
    if not is_update:
        existing = repos.products.find_one(
            {'sku': (data.get('sku') or '').strip(), **tenant_filter(company_id)})
        if existing:
            errors.append('SKU already exists.')
    return collect_errors(errors)


# --- lifecycle ------------------------------------------------------------

def _clean_product(data, existing=None):
    clean = {
        'name': data['name'].strip(),
        'sku': data['sku'].strip(),
        'description': (data.get('description') or '').strip(),
        'quantity': int(data.get('quantity', 0)),
        'price': float(data.get('price', 0)),
        'purchase_price': float(data.get('purchase_price', 0)),
        'category': (data.get('category') or '').strip(),
        'subcategory': (data.get('subcategory') or '').strip(),
        'package_type': (data.get('package_type') or '').strip(),
        'brand': (data.get('brand') or '').strip(),
        'supplier_id': _oid(data.get('supplier_id')),
        'supplier_name': (data.get('supplier_name') or '').strip(),
        'pack_size': float(data.get('pack_size', 0)),
        'pack_size_unit': (data.get('pack_size_unit') or '').strip(),
        'number_of_pack': int(data.get('number_of_pack', 0)),
        'quantity_min': int(data.get('quantity_min', 5)),
        'status': (data.get('status') or 'active').strip(),
        'photos': data.get('photos', []),
        'company_id': _oid(data.get('company_id')),
    }
    if existing is None:
        clean['quantity'] = int(data.get('quantity', 0))
    return clean


def create(data, user_id, company_id):
    payload = dict(data)
    payload['company_id'] = company_id
    clean = _clean_product(payload)
    clean['quantity'] = int(data.get('quantity', 0))
    product_id = repos.products.create(clean)
    logger.info('Product created: %s (sku=%s, id=%s, company=%s, by=%s)',
                clean['name'], clean['sku'], product_id, company_id, user_id)
    record_movement(product_id, clean['name'], clean['sku'], 'in',
                    clean['quantity'], 0, clean['quantity'],
                    'Initial stock', user_id, company_id)
    _emit('inventory.product.created', company_id=company_id, user_id=user_id,
          act=activity('product', '', clean['sku'], 'created'),
          payload={'id': product_id, 'sku': clean['sku']})
    return product_id


def update(product_id, data, user_id, company_id):
    product = repos.products.find_by_id(product_id)
    if not product:
        return None
    if str(product.get('company_id', '')) != str(company_id):
        return None
    old_qty = product.get('quantity', 0)
    payload = dict(data)
    payload['company_id'] = product.get('company_id')
    clean = _clean_product(payload, existing=product)
    if 'photos' not in payload:
        clean.pop('photos', None)   # an update never clobbers stored photos
    clean['quantity'] = int(data.get('quantity', old_qty))
    repos.products.update(product_id, clean, touch_updated=True)
    new_qty = clean['quantity']
    diff = new_qty - old_qty
    if diff != 0:
        mv_type = 'in' if diff > 0 else 'out'
        record_movement(product_id, clean['name'], clean['sku'],
                        mv_type, abs(diff), old_qty, new_qty,
                        'Stock adjustment', user_id, company_id)
    logger.info('Product updated: %s (id=%s, by=%s)',
                clean['name'], product_id, user_id)
    _emit('inventory.product.updated', company_id=company_id, user_id=user_id,
          act=activity('product', product_id, clean['sku'], 'updated',
                       changes={'field': 'details', 'old_value': '',
                                'new_value': 'updated'}),
          payload={'id': product_id, 'sku': clean['sku']})
    return True


def delete(product_id, user_id, company_id):
    product = repos.products.find_by_id(product_id)
    if not product:
        return False
    if str(product.get('company_id', '')) != str(company_id):
        return False
    repos.products.delete(product_id)
    logger.info('Product deleted: %s (id=%s, by=%s)',
                product.get('name'), product_id, user_id)
    _emit('inventory.product.deleted', company_id=company_id, user_id=user_id,
          act=activity('product', product_id, product.get('sku', ''), 'deleted'),
          payload={'id': product_id, 'sku': product.get('sku', '')})
    return True


# --- stock ----------------------------------------------------------------

def deduct_stock(sku, quantity, company_id, reference='', user_id=None):
    product = repos.products.find_one({'sku': sku, **tenant_filter(company_id)})
    if not product:
        return False
    if product['quantity'] < quantity:
        return False
    new_qty = product['quantity'] - quantity
    repos.products.update(str(product['_id']), {'quantity': new_qty}, touch_updated=True)
    record_movement(str(product['_id']), product['name'], sku, 'out',
                    quantity, product['quantity'], new_qty,
                    reference or 'Invoice deduction', user_id, company_id)
    return True


def record_movement(product_id, product_name, sku, mv_type, quantity,
                    qty_before, qty_after, reason, user_id, company_id):
    """The monolith recorded movements as *activity events* only (its
    ``stock_movements`` collection was never written) — same here."""
    try:
        _emit('inventory.stock.adjusted', company_id=company_id,
              user_id=user_id,
              act=activity('product', product_id, sku, 'stock_movement',
                           changes={'quantity': quantity, 'reason': reason,
                                    'quantity_before': qty_before,
                                    'quantity_after': qty_after,
                                    'type': mv_type}),
              payload={'product_id': product_id, 'sku': sku,
                       'quantity': quantity, 'type': mv_type})
    except Exception:
        logger.exception('Could not record stock movement for %s', sku)


# --- reads used by the dashboards ----------------------------------------

def category_summary(company_id=None):
    pipeline = [
        {'$match': tenant_filter(company_id)},
        {'$group': {'_id': '$category', 'count': {'$sum': 1},
                    'total_qty': {'$sum': '$quantity'},
                    'total_value': {'$sum': {'$multiply': ['$quantity', '$price']}}}},
        {'$sort': {'_id': 1}},
    ]
    return repos.products.aggregate(pipeline)


def total_valuation(company_id=None):
    pipeline = [{'$match': tenant_filter(company_id)},
                {'$group': {'_id': None,
                            'total_value': {'$sum': {'$multiply': ['$quantity', '$price']}},
                            'total_products': {'$sum': 1},
                            'total_qty': {'$sum': '$quantity'}}}]
    result = repos.products.aggregate(pipeline)
    return result[0] if result else {'total_value': 0, 'total_products': 0, 'total_qty': 0}


def search(q, company_id=None, limit=10):
    query = {'$or': [{'sku': re.compile(re.escape(q), re.IGNORECASE)},
                     {'name': re.compile(re.escape(q), re.IGNORECASE)}]}
    if company_id:
        query.update(tenant_filter(company_id))
    return list(repos.products.coll.find(query).limit(limit))


def _oid(value):
    from si_common.ids import oid
    return oid(value)
