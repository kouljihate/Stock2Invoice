"""Dashboard widget slice for inventory: everything the dashboards read
from products/stock in one call, so the BFF renders with a single hop."""

from fastapi import APIRouter, Depends

from si_common.auth import Identity, make_require_company
from si_common.tenancy import scoped

from .. import repos, service
from ..serialize import product_out

router = APIRouter(tags=['dashboard'])

require_company = make_require_company('inventory')


@router.get('/dashboard/widgets')
def widgets(identity: Identity = Depends(require_company)):
    scope = scoped(identity)
    docs = repos.products.find_all_unpaginated(scope)
    low_stock = [product_out(p) for p in docs
                 if p.get('quantity', 0) <= p.get('quantity_min', 5)]

    categories = [{'_id': r.get('_id'), 'category': r.get('_id'),
                   'count': r.get('count', 0),
                   'total_qty': r.get('total_qty', 0),
                   'total_value': r.get('total_value', 0)}
                  for r in service.category_summary(identity.company_id)]

    movements = repos.movements.recent(10, scope)
    from ..serialize import movement_out
    return {
        'product_count': len(docs),
        'low_stock': low_stock,
        'valuation': service.total_valuation(identity.company_id),
        'category_summary': categories,
        'recent_movements': [movement_out(m) for m in movements],
    }
