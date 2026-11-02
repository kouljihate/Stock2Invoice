"""Activity-log projector: consumes every domain event and appends the ones
carrying an ``activity`` block to the ``events`` collection.

This replaces the ~30 inline ``EventService.record`` calls the monolith
scattered across its routes — each service now declares the activity intent
next to the write that caused it, and this consumer materialises it.
"""

import logging
import threading
import time
from datetime import datetime, timezone

from si_common.http import ServiceCallError, call
from si_common.ids import oid

from . import repos

logger = logging.getLogger(__name__)

# user_id -> (name, fetched_at); identity lookups are cached briefly so a
# busy feed does not turn into one HTTP call per row.
_NAME_TTL = 60
_names = {}
_names_lock = threading.Lock()


def resolve_user_name(user_id):
    if not user_id:
        return ''
    now = time.time()
    with _names_lock:
        hit = _names.get(user_id)
    if hit and now - hit[1] < _NAME_TTL:
        return hit[0]
    name = ''
    try:
        brief = call('identity', f'/internal/users/{user_id}', service_key=True)
        name = (brief or {}).get('name', '') or ''
    except ServiceCallError as exc:
        # Cosmetic only: write the row with an empty name rather than losing
        # it because identity was briefly unavailable.
        logger.warning('Could not resolve user %s: %s', user_id, exc)
    with _names_lock:
        _names[user_id] = (name, now)
    return name


def handle(event: dict):
    payload = event.get('payload') or {}
    act = payload.get('activity')
    if not act:
        return   # domain-only event: nothing belongs in the activity feed

    user_id = (event.get('actor') or {}).get('user_id')
    user_name = act.get('user_name') or resolve_user_name(user_id)

    try:
        created_at = datetime.fromisoformat(event.get('occurred_at'))
    except (TypeError, ValueError):
        created_at = datetime.now(timezone.utc)

    repos.events.create({
        'company_id': oid(event.get('company_id')),
        'entity_type': act.get('entity_type', ''),
        'entity_id': act.get('entity_id', ''),
        'entity_number': act.get('entity_number', ''),
        'action': act.get('action', ''),
        'changes': act.get('changes') or {},
        'user_id': oid(user_id),
        'user_name': user_name,
        'created_at': created_at,
    })
