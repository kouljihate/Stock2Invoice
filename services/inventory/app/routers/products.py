"""Product CRUD, catalog reads and stock summaries."""

import json

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request

from si_common.auth import (Identity, get_identity, make_require_company)

from .. import repos, service
from ..serialize import product_out

router = APIRouter(tags=['products'])

require_company = make_require_company('inventory')


def optional_identity(request: Request) -> Identity | None:
    return get_identity(request, 'inventory')


def _filters(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {}


@router.get('')
def list_products(filters: str | None = None, page: int = 1, per_page: int = 20,
                  identity: Identity = Depends(require_company)):
    docs, total = repos.products.find_all(
        page, per_page, service_scoped(identity, _filters(filters)))
    return {'items': [product_out(d) for d in docs], 'total': total}


@router.get('/catalog')
def catalog(filters: str | None = None, page: int = 1, per_page: int = 20,
            identity: Identity | None = Depends(optional_identity)):
    """Public eShop catalogue: anonymous sees every company's active
    products, a signed-in browser is pinned to its own company — exactly the
    monolith's ``allow_unscoped=True`` behaviour."""
    docs, total = repos.products.find_all(
        page, per_page, service_scoped(identity, _filters(filters),
                                       allow_unscoped=True))
    return {'items': [product_out(d) for d in docs], 'total': total}


@router.get('/count')
def count_products(filters: str | None = None,
                   identity: Identity = Depends(require_company)):
    return {'count': repos.products.count(service_scoped(identity, _filters(filters)))}


@router.get('/low-stock')
def low_stock(identity: Identity = Depends(require_company)):
    docs = repos.products.find_all_unpaginated(service_scoped(identity))
    items = [d for d in docs
             if d.get('quantity', 0) <= d.get('quantity_min', 5)]
    return {'items': [product_out(d) for d in items]}


@router.get('/summary/categories')
def category_summary(identity: Identity = Depends(require_company)):
    rows = service.category_summary(identity.company_id)
    # ``_id`` is the raw bucket key the dashboard template reads.
    return {'items': [{'_id': r.get('_id'), 'category': r.get('_id'),
                       'count': r.get('count', 0),
                       'total_qty': r.get('total_qty', 0),
                       'total_value': r.get('total_value', 0)} for r in rows]}


@router.get('/summary/valuation')
def valuation(identity: Identity = Depends(require_company)):
    return service.total_valuation(identity.company_id)


@router.get('/search')
def search(q: str = '', limit: int = 10,
           identity: Identity = Depends(require_company)):
    if not q.strip():
        return {'items': []}
    docs = service.search(q.strip(), identity.company_id, limit)
    return {'items': [product_out(d) for d in docs]}


@router.get('/sku/{sku}')
def by_sku(sku: str, identity: Identity = Depends(require_company)):
    """Sync SKU/price lookup used by sales-service when validating lines."""
    doc = repos.products.find_one({'sku': sku,
                                   **service_scoped(identity)})
    if not doc:
        raise HTTPException(status_code=404, detail=f'Product with SKU "{sku}" not found.')
    return product_out(doc)


@router.get('/id/{product_id}')
def by_id(product_id: str, public: bool = False,
          identity: Identity | None = Depends(optional_identity)):
    doc = repos.products.find_by_id(product_id)
    if not doc:
        raise HTTPException(status_code=404, detail='Product not found.')
    if identity and identity.company_id:
        if str(doc.get('company_id')) != identity.company_id:
            raise HTTPException(status_code=404, detail='Product not found.')
        return product_out(doc)
    if public:
        return product_out(doc)
    raise HTTPException(status_code=403, detail='Account is not linked to a company')


@router.post('/validate')
def validate_product(body: dict = Body(...),
                     identity: Identity = Depends(require_company)):
    data = body.get('data') or body
    return {'errors': service.validate(data, identity.company_id,
                                       bool(body.get('is_update'))
                                       if 'is_update' in body else False)}


@router.post('')
def create_product(body: dict = Body(...),
                   identity: Identity = Depends(require_company)):
    product_id = service.create(body, identity.user_id, identity.company_id)
    return {'id': product_id}


@router.patch('/{product_id}')
def update_product(product_id: str, body: dict = Body(...),
                   identity: Identity = Depends(require_company)):
    result = service.update(product_id, body, identity.user_id,
                            identity.company_id)
    if result is None:
        raise HTTPException(status_code=404, detail='Product not found.')
    return {'ok': True}


@router.delete('/{product_id}')
def delete_product(product_id: str,
                   identity: Identity = Depends(require_company)):
    if not service.delete(product_id, identity.user_id, identity.company_id):
        raise HTTPException(status_code=404, detail='Product not found.')
    return {'ok': True}


def service_scoped(identity, filters=None, allow_unscoped=False):
    from si_common.tenancy import scoped
    return scoped(identity, filters, allow_unscoped=allow_unscoped)
