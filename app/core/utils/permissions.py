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


def expand_permission(perm):
    if perm == '*':
        return ALL_PERMISSIONS
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
        wild = f'{module}.*'
        if wild in user_permissions:
            return True
        if '*' in user_permissions:
            return True
    return False
