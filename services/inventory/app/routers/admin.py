"""Platform-admin statistics for the collections inventory owns."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from si_common.auth import Identity, make_require_admin
from si_common.ids import tenant_filter

from .. import repos
from ..serialize import product_out

router = APIRouter(tags=['admin'])

require_admin = make_require_admin('inventory')


def _counts_by_company(collection):
    counts = {}
    for row in repos.products.db[collection].aggregate(
            [{'$group': {'_id': '$company_id', 'n': {'$sum': 1}}}]):
        if row['_id'] is not None:
            counts[str(row['_id'])] = row['n']
    return counts


@router.get('/admin/stats')
def admin_stats(_: Identity = Depends(require_admin)):
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0)
    return {
        'counters': {
            'product_count': _counts_by_company('products'),
            'movement_count': _counts_by_company('stock_movements'),
        },
        'today': {
            'movements': repos.movements.count({'created_at': {'$gte': today_start}}),
        },
        'collection_stats': {
            'products': repos.products.count(),
            'stock_movements': repos.movements.count(),
        },
    }


@router.get('/admin/companies/{company_id}/overview')
def company_overview(company_id: str, _: Identity = Depends(require_admin)):
    scope = tenant_filter(company_id)
    products_raw = list(repos.products.coll.find(scope)
                        .sort('created_at', -1).limit(50))
    products = [{
        'id': str(p['_id']), 'name': p.get('name'), 'sku': p.get('sku'),
        'quantity': p.get('quantity', 0), 'price': float(p.get('price', 0)),
        'category': p.get('category', ''),
        'stock_value': float(p.get('quantity', 0)) * float(p.get('price', 0)),
    } for p in products_raw]
    return {
        'product_count': repos.products.count(scope),
        'movement_count': repos.movements.count(scope),
        'products': products,
    }
