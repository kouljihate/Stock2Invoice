"""Dashboard widget slice for procurement: P2P counters, PO status chart and
overdue supplier bills, in one call."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from si_common.auth import Identity, make_require_company
from si_common.tenancy import scoped

from .. import repos
from ..serialize import payment_out, po_out, si_out

router = APIRouter(tags=['dashboard'])

require_company = make_require_company('procurement')


@router.get('/dashboard/widgets')
def widgets(identity: Identity = Depends(require_company)):
    scope = scoped(identity)
    now = datetime.now(timezone.utc)

    status_rows = list(repos.purchase_orders.aggregate([
        {'$match': scope},
        {'$group': {'_id': '$status', 'count': {'$sum': 1}}},
    ]))
    po_status_map = {r['_id']: r['count'] for r in status_rows}

    overdue_supplier = list(repos.supplier_invoices.coll.find({
        **scope, 'due_date': {'$lt': now},
        'status': {'$nin': ['paid', 'cancelled']},
    }).sort('due_date', 1))

    # Outflow chart: unpaid supplier bills grouped by due month (180 days).
    outflow = list(repos.supplier_invoices.aggregate([
        {'$match': {**scope, 'due_date': {'$gte': now - timedelta(days=180)}}},
        {'$group': {'_id': {'$dateToString': {'format': '%Y-%m', 'date': '$due_date'}},
                    'outflow': {'$sum': {'$cond': [{'$ne': ['$status', 'paid']},
                                                    '$total', 0]}},
                    'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}},
    ]))

    pending_grs = list(repos.purchase_orders.coll.find(
        {**scope, 'status': {'$nin': ['received', 'cancelled']}}
    ).sort('created_at', -1).limit(10))

    return {
        'supplier_count': repos.suppliers.count(scope),
        'po_count': repos.purchase_orders.count(scope),
        'gr_count': repos.goods_receipts.count(scope),
        'si_count': repos.supplier_invoices.count(scope),
        'payment_count': repos.payments.count(scope),
        'po_status_map': po_status_map,
        'overdue_supplier': [si_out(s) for s in overdue_supplier],
        'outflow': [{'month': o['_id'], 'outflow': float(o['outflow']),
                     'count': o['count']} for o in outflow],
        'pending_grs': [po_out(p) for p in pending_grs],
        'recent_pos': [po_out(p) for p in
                       repos.purchase_orders.recent(5, scope)],
        'recent_sis': [si_out(s) for s in
                       repos.supplier_invoices.recent(5, scope)],
        'recent_payments': [payment_out(p) for p in repos.payments.recent(5, scope)],
    }
