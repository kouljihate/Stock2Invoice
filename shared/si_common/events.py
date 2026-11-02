"""Domain-event construction.

Events are written to the service's ``outbox`` (see ``messaging.emit``) and
published to the ``domain.events`` topic exchange. When an event should also
appear in the cross-service activity log, its payload carries an
``activity`` block and workers-service projects it into ``events`` — this
replaces the monolith's inline ``EventService.record`` calls.
"""

from .messaging import emit, new_event  # noqa: F401  (re-export)


def emit_event(db, event_type, *, source, company_id=None, payload=None,
               activity=None, actor_user_id=None, correlation_id=None):
    """Build + enqueue one event. Returns the event id."""
    body = dict(payload or {})
    if activity is not None:
        body['activity'] = activity
    event = new_event(
        event_type,
        company_id=company_id,
        payload=body,
        source=source,
        actor_user_id=actor_user_id,
        correlation_id=correlation_id,
    )
    return emit(db, event)


def activity(entity_type, entity_id, entity_number, action, changes=None):
    """Activity-log row intent, mirroring the monolith's EventService.record."""
    return {
        'entity_type': entity_type,
        'entity_id': str(entity_id) if entity_id else '',
        'entity_number': str(entity_number) if entity_number is not None else '',
        'action': action,
        'changes': changes or {},
    }
