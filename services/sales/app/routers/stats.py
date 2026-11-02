"""Platform-admin statistics for the collections sales owns."""

from fastapi import APIRouter, Depends

from si_common.auth import Identity, make_require_admin
from si_common.ids import tenant_filter

from .. import repos

router = APIRouter(tags=['admin'])

require_admin = make_require_admin('sales')


def _counts_by_company(collection):
    counts = {}
    for row in repos.invoices.db[collection].aggregate(
            [{'$group': {'_id': '$company_id', 'n': {'$sum': 1}}}]):
        if row['_id'] is not None:
            counts[str(row['_id'])] = row['n']
    return counts


@router.get('/admin/stats')
def admin_stats(_: Identity = Depends(require_admin)):
    revenue = {}
    for row in repos.invoices.db['invoices'].aggregate([
        {'$match': {'status': 'paid'}},
        {'$group': {'_id': '$company_id', 'total': {'$sum': '$total'}}},
    ]):
        if row['_id'] is not None:
            revenue[str(row['_id'])] = round(float(row['total']), 2)
    return {
        'counters': {
            'order_count': _counts_by_company('orders'),
            'invoice_count': _counts_by_company('invoices'),
        },
        'revenue_by_company': revenue,
        'collection_stats': {
            'orders': repos.orders.count(),
            'invoices': repos.invoices.count(),
            'customer_quotes': repos.quotes.count(),
            'delivery_notes': repos.delivery_notes.count(),
        },
    }


@router.get('/admin/companies/{company_id}/overview')
def company_overview(company_id: str, _: Identity = Depends(require_admin)):
    scope = tenant_filter(company_id)
    orders_raw = list(repos.orders.coll.find(scope).sort('created_at', -1).limit(50))
    invoices_raw = list(repos.invoices.coll.find(scope).sort('created_at', -1).limit(50))

    def _day(value):
        return value.isoformat()[:10] if value else ''

    orders = [{
        'id': str(o['_id']), 'order_number': o.get('order_number'),
        'customer_name': o.get('customer_name'),
        'total': float(o.get('total', 0)),
        'status': o.get('status', 'pending'),
        'created_at': _day(o.get('created_at')),
    } for o in orders_raw]
    invoices = [{
        'id': str(inv['_id']), 'invoice_number': inv.get('invoice_number'),
        'customer_name': inv.get('customer_name'),
        'total': float(inv.get('total', 0)),
        'status': inv.get('status', 'draft'),
        'created_at': _day(inv.get('created_at')),
    } for inv in invoices_raw]
    return {
        'order_count': repos.orders.count(scope),
        'invoice_count': repos.invoices.count(scope),
        'orders': orders,
        'invoices': invoices,
    }
