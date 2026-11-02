"""Delivery notes: numbering, CRUD, activity."""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException

from si_common.auth import Identity, make_require_company
from si_common.events import activity, emit_event
from si_common.ids import oid
from si_common.tenancy import scoped

from .. import repos
from ..serialize import delivery_note_out

logger = logging.getLogger(__name__)
router = APIRouter(tags=['delivery-notes'])

require_company = make_require_company('sales')


def _emit(identity, event_type, act=None, payload=None):
    emit_event(repos.delivery_notes.db, event_type, source='sales',
               company_id=identity.company_id, actor_user_id=identity.user_id,
               activity=act, payload=payload)


def _filters(raw):
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {}


@router.get('')
def list_delivery_notes(filters: str | None = None, page: int = 1,
                        per_page: int = 20,
                        identity: Identity = Depends(require_company)):
    docs, total = repos.delivery_notes.find_all(
        page, per_page, scoped(identity, _filters(filters)))
    return {'items': [delivery_note_out(d) for d in docs], 'total': total}


@router.post('')
def create_delivery_note(body: dict = Body(...),
                         identity: Identity = Depends(require_company)):
    payload = dict(body)
    count = repos.delivery_notes.count(scoped(identity))
    payload['dn_number'] = f"DN-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
    payload['company_id'] = oid(identity.company_id)
    payload['created_by'] = oid(identity.user_id)
    if payload.get('order_id'):
        payload['order_id'] = oid(payload['order_id'])
    dn_id = repos.delivery_notes.create(payload)
    _emit(identity, 'sales.delivery_note.created',
          act=activity('delivery_note', '', payload['dn_number'], 'created'),
          payload={'id': dn_id, 'dn_number': payload['dn_number']})
    return {'id': dn_id, 'dn_number': payload['dn_number']}


@router.delete('/{dn_id}')
def delete_delivery_note(dn_id: str, identity: Identity = Depends(require_company)):
    doc = repos.delivery_notes.find_by_id(dn_id, scoped(identity))
    if not doc:
        raise HTTPException(status_code=404, detail='Delivery note not found.')
    repos.delivery_notes.delete(dn_id)
    _emit(identity, 'sales.delivery_note.deleted',
          act=activity('delivery_note', dn_id, doc.get('dn_number', ''), 'deleted'),
          payload={'id': dn_id, 'dn_number': doc.get('dn_number', '')})
    return {'ok': True}
