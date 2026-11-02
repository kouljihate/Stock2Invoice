"""Platform-admin statistics for the collections procurement owns."""

from fastapi import APIRouter, Depends

from si_common.auth import Identity, make_require_admin

from .. import repos

router = APIRouter(tags=['admin'])

require_admin = make_require_admin('procurement')


@router.get('/admin/stats')
def admin_stats(_: Identity = Depends(require_admin)):
    counts = {}
    for row in repos.purchase_orders.db['purchase_orders'].aggregate(
            [{'$group': {'_id': '$company_id', 'n': {'$sum': 1}}}]):
        if row['_id'] is not None:
            counts[str(row['_id'])] = row['n']
    return {
        'counters': {'po_count': counts},
        'collection_stats': {
            'purchase_orders': repos.purchase_orders.count(),
            'supplier_invoices': repos.supplier_invoices.count(),
        },
    }
