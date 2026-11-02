"""Supplier CRUD + activity rows."""

import json

from fastapi import APIRouter, Body, Depends, HTTPException

from si_common.auth import Identity, make_require_company
from si_common.ids import oid
from si_common.tenancy import scoped

from .. import activity, repos
from ..serialize import supplier_out

router = APIRouter(tags=['suppliers'])

require_company = make_require_company('procurement')


def _filters(raw):
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {}


@router.get('')
def list_suppliers(filters: str | None = None, page: int = 1, per_page: int = 20,
                   identity: Identity = Depends(require_company)):
    docs, total = repos.suppliers.find_all(
        page, per_page, scoped(identity, _filters(filters)), sort=('name', 1))
    return {'items': [supplier_out(d) for d in docs], 'total': total}


@router.get('/unpaginated')
def all_suppliers(filters: str | None = None,
                  identity: Identity = Depends(require_company)):
    docs = repos.suppliers.find_all_unpaginated(scoped(identity, _filters(filters)))
    docs.sort(key=lambda s: (s.get('name') or '').lower())
    return {'items': [supplier_out(d) for d in docs]}


@router.get('/id/{supplier_id}')
def get_supplier(supplier_id: str, identity: Identity = Depends(require_company)):
    doc = repos.suppliers.find_by_id(supplier_id, scoped(identity))
    if not doc:
        raise HTTPException(status_code=404, detail='Supplier not found.')
    return supplier_out(doc)


@router.post('')
def create_supplier(body: dict = Body(...), identity: Identity = Depends(require_company)):
    data = dict(body)
    data['company_id'] = oid(identity.company_id)
    supplier_id = repos.suppliers.create(data)
    activity.crud_event('supplier', identity, 'created', supplier_id,
                        data.get('name', ''))
    return {'id': supplier_id}


@router.patch('/{supplier_id}')
def update_supplier(supplier_id: str, body: dict = Body(...),
                    identity: Identity = Depends(require_company)):
    if not repos.suppliers.find_by_id(supplier_id, scoped(identity)):
        raise HTTPException(status_code=404, detail='Supplier not found.')
    repos.suppliers.update(supplier_id, dict(body))
    activity.crud_event('supplier', identity, 'updated', supplier_id,
                        body.get('name', ''),
                        changes={'field': 'details', 'old_value': '',
                                 'new_value': 'updated'})
    return {'ok': True}


@router.delete('/{supplier_id}')
def delete_supplier(supplier_id: str, identity: Identity = Depends(require_company)):
    doc = repos.suppliers.find_by_id(supplier_id, scoped(identity))
    if not doc:
        raise HTTPException(status_code=404, detail='Supplier not found.')
    repos.suppliers.delete(supplier_id)
    activity.crud_event('supplier', identity, 'deleted', supplier_id,
                        doc.get('name', ''))
    return {'ok': True}
