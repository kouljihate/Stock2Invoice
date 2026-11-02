"""Dashboard widget slice for sales: quote-to-cash counters, charts and
lists the dashboards render, in one call."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from si_common.auth import Identity, make_require_company
from si_common.tenancy import scoped

from .. import repos
from ..serialize import (delivery_note_out, invoice_out, order_out,
                         quote_out)

router = APIRouter(tags=['dashboard'])

require_company = make_require_company('sales')


@router.get('/dashboard/widgets')
def widgets(identity: Identity = Depends(require_company)):
    scope = scoped(identity)
    now = datetime.now(timezone.utc)

    # Cashflow: monthly paid inflow from customer invoices (180 days).
    cashflow = list(repos.invoices.aggregate([
        {'$match': {**scope, 'created_at': {'$gte': now - timedelta(days=180)}}},
        {'$group': {'_id': {'$dateToString': {'format': '%Y-%m', 'date': '$created_at'}},
                    'inflow': {'$sum': {'$cond': [{'$eq': ['$status', 'paid']},
                                                   '$total', 0]}},
                    'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}},
    ]))

    overdue = list(repos.invoices.coll.find({
        **scope, 'due_date': {'$lt': now},
        'status': {'$nin': ['paid', 'cancelled']},
    }).sort('due_date', 1))

    active_quotes = list(repos.quotes.coll.find(
        {**scope, 'status': {'$in': ['draft', 'sent']}}
    ).sort('valid_until', 1).limit(10))

    orders_ready = list(repos.orders.coll.find(
        {**scope, 'status': 'confirmed'}
    ).sort('created_at', -1).limit(10))

    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0,
                             microsecond=0)

    def _paid_total(since):
        rows = repos.invoices.aggregate([
            {'$match': {**scope, 'status': 'paid', 'created_at': {'$gte': since}}},
            {'$group': {'_id': None, 'total': {'$sum': '$total'}}},
        ])
        return round(rows[0]['total'], 2) if rows else 0.0

    return {
        'customer_count': repos.customers.count(scope),
        'quote_count': repos.quotes.count(scope),
        'order_count': repos.orders.count(scope),
        'dn_count': repos.delivery_notes.count(scope),
        'month_sales': _paid_total(month_start),
        'year_sales': _paid_total(year_start),
        'invoice_counts': {
            'total': repos.invoices.count(scope),
            'draft': repos.invoices.count({**scope, 'status': 'draft'}),
            'sent': repos.invoices.count({**scope, 'status': 'sent'}),
            'paid': repos.invoices.count({**scope, 'status': 'paid'}),
            'cancelled': repos.invoices.count({**scope, 'status': 'cancelled'}),
        },
        'recent_invoices': [invoice_out(i) for i in repos.invoices.recent(5, scope)],
        'cashflow': [{'month': c['_id'], 'inflow': float(c['inflow']),
                      'count': c['count']} for c in cashflow],
        'overdue_invoices': [invoice_out(i) for i in overdue],
        'overdue_total': sum(float(i.get('total', 0)) for i in overdue),
        'active_quotes': [quote_out(q) for q in active_quotes],
        'orders_ready': [order_out(o) for o in orders_ready],
        'recent_quotes': [quote_out(q) for q in repos.quotes.recent(5, scope)],
        'recent_orders': [order_out(o) for o in repos.orders.recent(5, scope)],
        'recent_dns': [delivery_note_out(d)
                       for d in repos.delivery_notes.recent(5, scope)],
    }
