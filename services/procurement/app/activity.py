"""Activity/domain events published by procurement-service."""

from si_common.events import activity, emit_event

from . import repos


def emit(event_type, *, identity, act=None, payload=None):
    return emit_event(
        repos.suppliers.db, event_type, source='procurement',
        company_id=identity.company_id, actor_user_id=identity.user_id,
        activity=act, payload=payload)


def crud_event(entity, identity, action, entity_id, entity_number, changes=None):
    """Standard entity lifecycle event with its activity row."""
    return emit(
        f'procurement.{entity}.{action}', identity=identity,
        act=activity(entity, entity_id, entity_number, action, changes=changes),
        payload={'id': str(entity_id or ''), 'number': entity_number,
                 'action': action})
