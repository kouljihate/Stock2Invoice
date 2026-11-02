"""Stock movement history reads (the monolith never wrote rows here — the
collection is populated only by migrated legacy data)."""

import json

from fastapi import APIRouter, Depends

from si_common.auth import Identity, make_require_company
from si_common.ids import oid

from .. import repos
from ..serialize import movement_out

router = APIRouter(tags=['movements'])

require_company = make_require_company('inventory')


@router.get('')
def list_movements(filters: str | None = None, page: int = 1, per_page: int = 20,
                   product_id: str | None = None,
                   identity: Identity = Depends(require_company)):
    query = {}
    if filters:
        try:
            query = json.loads(filters)
        except ValueError:
            query = {}
    if product_id:
        query['product_id'] = oid(product_id)
    from si_common.tenancy import scoped
    docs, total = repos.movements.find_all(page, per_page, scoped(identity, query))
    return {'items': [movement_out(d) for d in docs], 'total': total}


@router.get('/recent')
def recent_movements(limit: int = 10,
                     identity: Identity = Depends(require_company)):
    from si_common.tenancy import scoped
    docs = repos.movements.recent(limit, scoped(identity))
    return {'items': [movement_out(d) for d in docs]}
