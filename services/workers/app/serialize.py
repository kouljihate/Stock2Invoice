"""Activity-row shape — exact port of ``EventModel.to_dict``."""

from si_common.ids import as_str, iso


def event_out(ev):
    if not ev:
        return None
    return {
        'id': str(ev['_id']),
        'company_id': as_str(ev.get('company_id')),
        'entity_type': ev.get('entity_type', ''),
        'entity_id': ev.get('entity_id', ''),
        'entity_number': ev.get('entity_number', ''),
        'action': ev.get('action', ''),
        'changes': ev.get('changes', {}),
        'user_id': as_str(ev.get('user_id')),
        'user_name': ev.get('user_name', ''),
        'created_at': iso(ev.get('created_at')),
    }
