"""Canonical RBAC catalogue and role definitions.

This is the contract shared by the BFF's route gate and identity-service's
seed: both must agree on which permissions exist and which roles grant what.
``app/core/utils/permissions.py`` and ``app/core/utils/bootstrap.py`` in the
BFF re-export from here so existing imports and tests keep working.
"""

ALL_PERMISSIONS = [
    # Products / inventory catalogue
    'product.view', 'product.create', 'product.edit', 'product.delete', 'product.price_edit',
    # Stock movements
    'stock.view', 'stock.adjust', 'stock.transfer', 'stock.audit',
    # Customers
    'customer.view', 'customer.create', 'customer.edit', 'customer.delete',
    # Customer quotes (quote-to-cash)
    'quote.view', 'quote.create', 'quote.edit', 'quote.send', 'quote.validate', 'quote.delete',
    # Sales orders
    'order.view', 'order.create', 'order.edit', 'order.cancel', 'order.delete', 'order.view_own',
    # Delivery notes
    'delivery_note.view', 'delivery_note.create', 'delivery_note.delete',
    # Customer invoices
    'invoice.view', 'invoice.create', 'invoice.edit', 'invoice.delete', 'invoice.refund',
    'invoice.view_own',
    # Suppliers (procure-to-pay)
    'supplier.view', 'supplier.create', 'supplier.edit', 'supplier.delete',
    'purchase_order.view', 'purchase_order.create', 'purchase_order.send', 'purchase_order.delete',
    'goods_receipt.view', 'goods_receipt.create', 'goods_receipt.edit', 'goods_receipt.delete',
    'supplier_invoice.view', 'supplier_invoice.create', 'supplier_invoice.validate',
    'supplier_invoice.delete',
    'payment.view', 'payment.create',
    'p2p.view',
    # Services
    'service.view', 'service.create', 'service.schedule', 'service.close',
    # Administration
    'user.view', 'user.manage', 'role.manage', 'settings.update',
    # EShop
    'eshop.view', 'eshop.administration', 'eshop.link',
    # Cross-cutting / platform level
    'general.companies', 'general.allusers', 'general.activities',
]

# Every permission except the two platform-level ones reserved for the
# super-admin panel (all companies / all users).
_MANAGER_EXCLUDED = {'general.companies', 'general.allusers'}

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

# The two profiles this application is built around:
#   Admin      — the single platform administrator (exactly one account),
#                who manages every other user profile.
#   PME-Admin  — the owner of one PME: full control of that company's own
#                stock, customers and users, and nothing outside it.
# 'Manager' and 'Customer' remain assignable inside a company.
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


def expand_permission(perm):
    if perm == '*':
        return list(ALL_PERMISSIONS)
    if perm.endswith('.*'):
        prefix = perm[:-2]
        return [p for p in ALL_PERMISSIONS if p.startswith(prefix)]
    return [perm]


def get_effective_permissions(role_permissions):
    result = set()
    for p in role_permissions:
        result.update(expand_permission(p))
    return list(result)


def has_permission(user_permissions, permission):
    if permission in user_permissions:
        return True
    parts = permission.split('.')
    if len(parts) == 2:
        module = parts[0]
        if f'{module}.*' in user_permissions:
            return True
        if '*' in user_permissions:
            return True
    return False
