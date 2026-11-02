"""Customer CRUD + activity rows (the route layer used to write these)."""

from fastapi import APIRouter, Body, Depends, HTTPException

from si_common.auth import Identity, make_require_company
from si_common.events import activity, emit_event
from si_common.ids import oid
from si_common.tenancy import scoped

from .. import repos
from ..serialize import customer_out

router = APIRouter(tags=['customers'])

require_company = make_require_company('sales')


def _emit(identity, act, payload=None):
    emit_event(repos.customers.db, 'sales.customer', source='sales',
               company_id=identity.company_id, actor_user_id=identity.user_id,
               activity=act, payload=payload)


@router.get('')
def list_customers(filters: str | None = None, page: int = 1, per_page: int = 20,
                   identity: Identity = Depends(require_company)):
    import json
    query = {}
    if filters:
        try:
            query = json.loads(filters)
        except ValueError:
            query = {}
    docs, total = repos.customers.find_all(
        page, per_page, scoped(identity, query), sort=('name', 1))
    return {'items': [customer_out(d) for d in docs], 'total': total}


@router.get('/unpaginated')
def all_customers(filters: str | None = None,
                  identity: Identity = Depends(require_company)):
    import json
    query = {}
    if filters:
        try:
            query = json.loads(filters)
        except ValueError:
            query = {}
    docs = repos.customers.find_all_unpaginated(scoped(identity, query))
    docs.sort(key=lambda c: (c.get('name') or '').lower())
    return {'items': [customer_out(d) for d in docs]}


@router.get('/id/{customer_id}')
def get_customer(customer_id: str, identity: Identity = Depends(require_company)):
    doc = repos.customers.find_by_id(customer_id, scoped(identity))
    if not doc:
        raise HTTPException(status_code=404, detail='Customer not found.')
    return customer_out(doc)


@router.post('')
def create_customer(body: dict = Body(...), identity: Identity = Depends(require_company)):
    data = dict(body)
    data['company_id'] = oid(identity.company_id)
    customer_id = repos.customers.create(data)
    _emit(identity,
          activity('customer', '', data.get('name', ''), 'created'),
          {'id': customer_id, 'name': data.get('name', '')})
    return {'id': customer_id}


@router.patch('/{customer_id}')
def update_customer(customer_id: str, body: dict = Body(...),
                    identity: Identity = Depends(require_company)):
    if not repos.customers.find_by_id(customer_id, scoped(identity)):
        raise HTTPException(status_code=404, detail='Customer not found.')
    repos.customers.update(customer_id, dict(body))
    _emit(identity,
          activity('customer', customer_id, body.get('name', ''), 'updated',
                   changes={'field': 'details', 'old_value': '',
                            'new_value': 'updated'}),
          {'id': customer_id, 'name': body.get('name', '')})
    return {'ok': True}


@router.delete('/{customer_id}')
def delete_customer(customer_id: str, identity: Identity = Depends(require_company)):
    doc = repos.customers.find_by_id(customer_id, scoped(identity))
    if not doc:
        raise HTTPException(status_code=404, detail='Customer not found.')
    repos.customers.delete(customer_id)
    _emit(identity,
          activity('customer', customer_id, doc.get('name', ''), 'deleted'),
          {'id': customer_id, 'name': doc.get('name', '')})
    return {'ok': True}
