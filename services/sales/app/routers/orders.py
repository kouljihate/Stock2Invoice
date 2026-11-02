"""Customer order endpoints; business logic lives in ``app.orders``."""

import json

from fastapi import APIRouter, Body, Depends, HTTPException

from si_common.auth import Identity, make_require_company
from si_common.tenancy import scoped

from .. import orders as service
from ..serialize import order_out

router = APIRouter(tags=['orders'])

require_company = make_require_company('sales')


def _filters(raw):
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {}


@router.get('')
def list_orders(filters: str | None = None, page: int = 1, per_page: int = 20,
                identity: Identity = Depends(require_company)):
    items, total = service.list(page, per_page, _filters(filters), identity)
    return {'items': items, 'total': total}


@router.get('/recent')
def recent_orders(limit: int = 5, identity: Identity = Depends(require_company)):
    return {'items': service.get_recent(limit, identity)}


@router.get('/counts')
def order_counts(identity: Identity = Depends(require_company)):
    return service.get_counts(identity)


@router.get('/id/{order_id}')
def get_order(order_id: str, identity: Identity = Depends(require_company)):
    order = service.get_by_id(order_id, identity)
    if not order:
        raise HTTPException(status_code=404, detail='Order not found.')
    return order


@router.post('/validate')
def validate_order(body: dict = Body(...),
                   identity: Identity = Depends(require_company)):
    data = body.get('data') or body
    return {'errors': service.validate(data, identity)}


@router.post('')
def create_order(body: dict = Body(...), identity: Identity = Depends(require_company)):
    order_id, order_number = service.create(body, identity)
    return {'id': order_id, 'order_number': order_number}


@router.patch('/{order_id}')
def update_order(order_id: str, body: dict = Body(...),
                 identity: Identity = Depends(require_company)):
    result = service.update(order_id, body, identity)
    if result is None:
        raise HTTPException(status_code=404, detail='Order not found.')
    return {'ok': True}


@router.delete('/{order_id}')
def delete_order(order_id: str, identity: Identity = Depends(require_company)):
    from .. import repos
    from si_common.events import activity, emit_event
    doc = repos.orders.find_by_id(order_id, scoped(identity))
    if not doc:
        raise HTTPException(status_code=404, detail='Order not found.')
    repos.orders.delete(order_id)
    emit_event(repos.orders.db, 'sales.order.deleted', source='sales',
               company_id=identity.company_id, actor_user_id=identity.user_id,
               activity=activity('order', order_id,
                                 doc.get('order_number', ''), 'deleted'),
               payload={'id': order_id,
                        'order_number': doc.get('order_number', '')})
    return {'ok': True}
