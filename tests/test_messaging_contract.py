# -*- coding: utf-8 -*-
"""Broker-free contract tests for the microservices event path.

No RabbitMQ, no Mongo: the outbox collection is stubbed and pika is only
imported, never connected. These pin the envelope shape every service
publishes/consumes, the retry-ladder accounting, and the BFF payload
sanitizer used for the workers-service PDF call.
"""

import os
import sys
from datetime import datetime, timezone
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from si_common.events import activity, emit_event, new_event
from si_common.messaging import RETRY_LADDER, _retry_count


class _StubCollection:
    def __init__(self):
        self.docs = []

    def insert_one(self, doc):
        self.docs.append(doc)


class _StubDb:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        return self.collections.setdefault(name, _StubCollection())


def test_new_event_envelope_shape():
    e1 = new_event('sales.invoice.paid', company_id='c1',
                   payload={'n': 1}, source='bff', actor_user_id='u9')
    e2 = new_event('sales.invoice.paid', company_id='c1', source='bff')
    assert e1['type'] == 'sales.invoice.paid'
    assert e1['source'] == 'bff'
    assert e1['company_id'] == 'c1'
    assert e1['actor'] == {'user_id': 'u9'}
    assert e1['payload'] == {'n': 1}
    assert e2['payload'] == {}
    assert e1['event_id'] != e2['event_id']  # unique per event
    datetime.fromisoformat(e1['occurred_at'])  # parseable timestamp


def test_emit_event_writes_pending_outbox_row():
    db = _StubDb()
    event_id = emit_event(
        db, 'sales.invoice.paid', source='bff', company_id='c1',
        payload={'invoice_number': 'INV-1'},
        activity=activity('invoice', 'abc', 'INV-1', 'paid'),
        actor_user_id='u9',
    )
    assert event_id
    rows = db['outbox'].docs
    assert len(rows) == 1
    row = rows[0]
    assert row['_id'] == event_id
    assert row['routing_key'] == 'sales.invoice.paid'
    assert row['published_at'] is None  # relay picks it up
    assert row['attempts'] == 0
    assert row['event']['payload']['activity']['action'] == 'paid'


def test_retry_count_reads_x_death_headers():
    assert _retry_count(SimpleNamespace(headers=None)) == 0
    assert _retry_count(SimpleNamespace(headers={})) == 0
    props = SimpleNamespace(headers={'x-death': [
        {'count': 1, 'queue': 'svc.events.retry.5s'},
        {'count': 2, 'queue': 'svc.events.retry.30s'},
    ]})
    assert _retry_count(props) == 2
    # Ladder length decides when a message is parked on the DLQ.
    assert len(RETRY_LADDER) == 3


def test_pdf_payload_sanitizer_is_json_plain():
    from bson import ObjectId

    from app.core.services.pdf_service import _json_safe

    payload = _json_safe({
        '_id': ObjectId('68f000000000000000000001'),
        'when': datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc),
        'items': [{'_id': ObjectId('68f000000000000000000002'), 'qty': 2}],
        'raw': b'\xff binary',
    })
    import json

    assert json.dumps(payload)  # must not raise
    assert payload['_id'] == '68f000000000000000000001'
    assert payload['items'][0]['_id'] == '68f000000000000000000002'
    assert payload['when'].startswith('2026-11-03')
