"""Supplier payments (P2P closing step)."""

import json
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException

from si_common.auth import Identity, make_require_company
from si_common.ids import oid
from si_common.tenancy import scoped

from .. import activity, repos
from ..serialize import payment_out

router = APIRouter(tags=['payments'])

require_company = make_require_company('procurement')


def _filters(raw):
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {}


@router.get('')
def list_payments(filters: str | None = None, page: int = 1, per_page: int = 20,
                  identity: Identity = Depends(require_company)):
    docs, total = repos.payments.find_all(
        page, per_page, scoped(identity, _filters(filters)))
    return {'items': [payment_out(d) for d in docs], 'total': total}


@router.post('')
def create_payment(body: dict = Body(...), identity: Identity = Depends(require_company)):
    payload = dict(body)
    count = repos.payments.count(scoped(identity))
    payload['payment_number'] = f"PMT-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
    payload.setdefault('status', 'pending')
    payload['company_id'] = oid(identity.company_id)
    payload['created_by'] = oid(identity.user_id)
    for key in ('supplier_id', 'invoice_id'):
        if payload.get(key):
            payload[key] = oid(payload[key])
    pmt_id = repos.payments.create(payload)
    activity.crud_event('payment', identity, 'created', pmt_id,
                        payload['payment_number'])
    return {'id': pmt_id, 'payment_number': payload['payment_number']}
