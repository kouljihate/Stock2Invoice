"""Repositories + index definitions owned by workers-service."""

from si_common.crud import Repository
from si_common.db import ensure_indexes

events = Repository('workers', 'events')

# Ported from the monolith's bootstrap for the events collection.
INDEXES = {
    'events': [
        ([('company_id', 1), ('created_at', -1)], {'name': 'events_company_created'}),
        ([('user_id', 1), ('created_at', -1)], {'name': 'events_user_created'}),
    ],
}


def ensure_all():
    return ensure_indexes('workers', INDEXES)
