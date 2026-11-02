"""Public shapes for identity documents.

``user_out`` returns an *enriched raw* document: every stored field except
the password, with ``_id`` stringified, timestamps ISO, plus ``id``,
``role_names`` and expanded ``permissions``. The BFF reads arbitrary fields
(``phone`` in the profile wizard), so nothing but the hash may be dropped.
"""

import time

from si_common.ids import as_str, iso
from si_common.rbac import get_effective_permissions

# role-name tuple -> (permissions, fetched_at); roles change rarely and the
# user endpoints are called once per rendered row.
_ROLE_CACHE = {}
_ROLE_CACHE_TTL = 30
_role_lock = __import__('threading').Lock()


def role_permissions(role_names):
    """Raw permission strings granted by a set of role names."""
    if not role_names:
        return []
    key = tuple(sorted(role_names))
    with _role_lock:
        hit = _ROLE_CACHE.get(key)
    if hit and time.time() - hit[1] < _ROLE_CACHE_TTL:
        return hit[0]
    from . import repos
    perms = []
    for name in role_names:
        role = repos.roles.find_one({'_id': name.lower()})
        if role and role.get('permissions'):
            perms.extend(role['permissions'])
    with _role_lock:
        _ROLE_CACHE[key] = (perms, time.time())
    return perms


def invalidate_role_cache():
    with _role_lock:
        _ROLE_CACHE.clear()


def effective_permissions(role_names):
    return get_effective_permissions(role_permissions(role_names))


def user_out(user):
    if not user:
        return None
    roles = list(user.get('roles') or [])
    out = {k: v for k, v in user.items() if k != 'password'}
    out['_id'] = str(user['_id'])
    out['id'] = out['_id']
    out['company_id'] = as_str(user.get('company_id'))
    out['created_at'] = iso(user.get('created_at'))
    out['updated_at'] = iso(user.get('updated_at'))
    out['roles'] = roles
    out['role_names'] = roles
    out['permissions'] = effective_permissions(roles)
    return out


def user_brief(user):
    """Minimal projection for cross-service lookups (no emails to workers? keep)."""
    if not user:
        return None
    return {'id': str(user['_id']), 'name': user.get('name', ''),
            'email': user.get('email', '')}


def company_out(c):
    if not c:
        return None
    return {
        'id': str(c['_id']),
        '_id': str(c['_id']),
        'name': c.get('name'),
        'slug': c.get('slug'),
        'logo': c.get('logo'),
        'address': c.get('address'),
        'city': c.get('city'),
        'phone': c.get('phone'),
        'email': c.get('email'),
        'contact_name': c.get('contact_name'),
        'ice': c.get('ice'),
        'rc': c.get('rc'),
        'if_tax': c.get('if_tax'),
        'cnss': c.get('cnss'),
        'patente': c.get('patente'),
        'rib': c.get('rib', ''),
        'tp': c.get('tp', c.get('patente', '')),
        'website': c.get('website'),
        'invoice_template': c.get('invoice_template', {}),
        'created_at': iso(c.get('created_at')),
    }


def role_out(role):
    if not role:
        return None
    return {
        'id': role['_id'],
        'name': role.get('name'),
        'description': role.get('description'),
        'permissions': role.get('permissions', []),
        'created_at': iso(role.get('created_at')),
        'updated_at': iso(role.get('updated_at')),
    }
