"""Idempotent boot-time work: RBAC role seed and MongoDB indexes.

Both operations are safe to run on every start. ``seed_roles`` upserts the
role definitions the application relies on ('Admin', 'PME-Admin', 'Manager',
'Customer') so that permission checks have something to evaluate against, and
``ensure_indexes`` creates the unique and compound indexes the queries need.

Failures are logged rather than raised so that a transient database problem
never prevents the app from booting; run ``flask bootstrap`` to do the same
work explicitly and see the output.
"""

import logging

from app.core.utils.permissions import ALL_PERMISSIONS

logger = logging.getLogger(__name__)

# Every permission except the two platform-level ones reserved for the
# super-admin panel (all companies / all users).
_MANAGER_EXCLUDED = {'general.companies', 'general.allusers'}

# The two profiles this application is built around:
#   Admin      — the single platform administrator (exactly one account),
#                who manages every other user profile.
#   PME-Admin  — the owner of one PME: full control of that company's own
#                stock, customers and users, and nothing outside it.
# 'Manager' and 'Customer' remain assignable inside a company.

# Regular company user: read everywhere plus create on the quote-to-cash side.
# No deletes, no user/role administration, no platform-level access.
_CUSTOMER_PERMISSIONS = [
    'product.view', 'stock.view',
    'customer.view', 'customer.create',
    'quote.view', 'quote.create', 'quote.edit', 'quote.send',
    'order.view', 'order.create', 'order.edit', 'order.view_own',
    'delivery_note.view', 'delivery_note.create',
    'invoice.view', 'invoice.create', 'invoice.view_own',
    'supplier.view', 'purchase_order.view', 'goods_receipt.view',
    'supplier_invoice.view', 'payment.view', 'p2p.view',
    'service.view',
    'user.view',
    'eshop.view',
    'general.activities',
]

ROLE_DEFINITIONS = {
    'Admin': {
        'description': 'Platform administrator — the single account that manages all user profiles',
        'permissions': ['*'],
    },
    'PME-Admin': {
        'description': 'PME owner — full access to their own company (stock, customers, users)',
        'permissions': [p for p in ALL_PERMISSIONS if p not in _MANAGER_EXCLUDED],
    },
    'Manager': {
        'description': 'Company administrator with access to all business operations',
        'permissions': [p for p in ALL_PERMISSIONS if p not in _MANAGER_EXCLUDED],
    },
    'Customer': {
        'description': 'Company user with view and create access',
        'permissions': list(_CUSTOMER_PERMISSIONS),
    },
}

# collection -> (unique index keys, additional index key lists)
INDEXES = {
    'users': [
        ([('email', 1)], {'unique': True, 'name': 'uniq_users_email'}),
        ([('company_id', 1)], {'name': 'users_company'}),
        ([('roles', 1)], {'name': 'users_roles'}),
    ],
    'companies': [
        ([('name', 1)], {'name': 'companies_name'}),
    ],
    'products': [
        ([('company_id', 1), ('sku', 1)], {'unique': True, 'name': 'uniq_products_company_sku'}),
        ([('company_id', 1), ('status', 1)], {'name': 'products_company_status'}),
        ([('company_id', 1), ('name', 1)], {'name': 'products_company_name'}),
    ],
    'invoices': [
        ([('company_id', 1), ('status', 1)], {'name': 'invoices_company_status'}),
        ([('company_id', 1), ('created_at', -1)], {'name': 'invoices_company_created'}),
        ([('company_id', 1), ('invoice_number', 1)], {'name': 'invoices_company_number'}),
    ],
    'orders': [
        ([('company_id', 1), ('status', 1)], {'name': 'orders_company_status'}),
        ([('company_id', 1), ('created_at', -1)], {'name': 'orders_company_created'}),
    ],
    'customer_quotes': [
        ([('company_id', 1), ('status', 1)], {'name': 'quotes_company_status'}),
        ([('company_id', 1), ('created_at', -1)], {'name': 'quotes_company_created'}),
    ],
    'stock_movements': [
        ([('company_id', 1), ('created_at', -1)], {'name': 'movements_company_created'}),
        ([('company_id', 1), ('sku', 1)], {'name': 'movements_company_sku'}),
    ],
    'purchase_orders': [
        ([('company_id', 1), ('status', 1)], {'name': 'po_company_status'}),
    ],
    'supplier_invoices': [
        ([('company_id', 1), ('status', 1)], {'name': 'supplier_inv_company_status'}),
    ],
    'delivery_notes': [
        ([('company_id', 1), ('created_at', -1)], {'name': 'dn_company_created'}),
    ],
    'goods_receipts': [
        ([('company_id', 1), ('created_at', -1)], {'name': 'gr_company_created'}),
    ],
    'payments': [
        ([('company_id', 1), ('created_at', -1)], {'name': 'payments_company_created'}),
    ],
    'suppliers': [
        ([('company_id', 1)], {'name': 'suppliers_company'}),
    ],
    'customers': [
        ([('company_id', 1)], {'name': 'customers_company'}),
    ],
    'events': [
        ([('company_id', 1), ('created_at', -1)], {'name': 'events_company_created'}),
        ([('user_id', 1), ('created_at', -1)], {'name': 'events_user_created'}),
    ],
}


def seed_roles():
    """Upsert the role definitions. Returns the number of roles written."""
    from app.extensions.db import mongo

    written = 0
    for name, spec in ROLE_DEFINITIONS.items():
        key = name.lower()
        existing = mongo.db['roles'].find_one({'_id': key}, {'permissions': 1})
        payload = {
            'name': name,
            'description': spec['description'],
            'permissions': list(spec['permissions']),
            'updated_at': _now(),
        }
        if existing and existing.get('permissions') == payload['permissions']:
            continue
        if not existing:
            payload['created_at'] = _now()
        mongo.db['roles'].update_one({'_id': key}, {'$set': payload}, upsert=True)
        written += 1
        logger.info('Seeded RBAC role %s (%d permissions)', name, len(payload['permissions']))
    return written


def ensure_indexes():
    """Create the indexes the query paths rely on. Returns index names written."""
    from app.extensions.db import mongo

    written = []
    for collection, specs in INDEXES.items():
        coll = mongo.db[collection]
        for keys, options in specs:
            try:
                name = coll.create_index(keys, **options)
            except Exception as exc:  # e.g. duplicate values block a unique index
                logger.warning('Index %s on %s not created: %s',
                               options.get('name'), collection, exc)
                continue
            written.append(name)
    return written


def bootstrap():
    """Run all idempotent boot work. Returns a dict of what happened."""
    result = {'roles': seed_roles(), 'indexes': ensure_indexes()}
    logger.info('Bootstrap complete: %s', result)
    return result


def _now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)
