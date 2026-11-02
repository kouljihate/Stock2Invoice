"""Idempotent RBAC seeding — ported from the monolith's ``bootstrap``.

The role definitions themselves live in the shared kernel
(``si_common.rbac``) so the BFF's route gate and this service can never
drift apart.
"""

import logging
from datetime import datetime, timezone

from si_common.rbac import ROLE_DEFINITIONS

from . import repos

logger = logging.getLogger(__name__)


def seed_roles():
    written = 0
    for name, spec in ROLE_DEFINITIONS.items():
        key = name.lower()
        existing = repos.roles.find_one({'_id': key})
        payload = {
            'name': name,
            'description': spec['description'],
            'permissions': list(spec['permissions']),
            'updated_at': datetime.now(timezone.utc),
        }
        if existing and existing.get('permissions') == payload['permissions']:
            continue
        if not existing:
            payload['created_at'] = datetime.now(timezone.utc)
        repos.roles.coll.update_one({'_id': key}, {'$set': payload}, upsert=True)
        written += 1
        logger.info('Seeded RBAC role %s (%d permissions)',
                    name, len(payload['permissions']))
    return written


def bootstrap():
    result = {'roles': seed_roles(), 'indexes': repos.ensure_all()}
    logger.info('Identity bootstrap complete: %s', result)
    return result
