ALL_PERMISSIONS = [
    'product.view', 'product.create', 'product.edit', 'product.delete', 'product.price_edit',
    'order.view', 'order.create', 'order.edit', 'order.cancel', 'order.view_own',
    'invoice.view', 'invoice.create', 'invoice.refund', 'invoice.view_own',
    'stock.view', 'stock.adjust', 'stock.transfer', 'stock.audit',
    'service.view', 'service.create', 'service.schedule', 'service.close',
    'user.view', 'user.manage', 'role.manage', 'settings.update',
    'p2p.view',
    'eshop.view', 'eshop.administration', 'eshop.link',
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