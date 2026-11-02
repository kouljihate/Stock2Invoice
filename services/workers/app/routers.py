"""Activity feed reads, PDF rendering, and admin statistics."""

import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Response
from fastapi import Request

from si_common.auth import (Identity, get_identity, make_require_admin,
                            make_require_identity, make_require_service)
from si_common.tenancy import scoped

from . import pdf, repos
from .serialize import event_out

router = APIRouter(tags=['events', 'pdf', 'admin'])

require_identity = make_require_identity('workers')
require_admin = make_require_admin('workers')
require_service = make_require_service('workers')


def _filters(raw):
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {}


@router.get('/events')
def list_events(filters: str | None = None, page: int = 1, per_page: int = 20,
                identity: Identity = Depends(require_identity)):
    query = scoped(identity, _filters(filters))
    docs, total = repos.events.find_all(page, per_page, query)
    return {'items': [event_out(d) for d in docs], 'total': total}


@router.post('/pdf/invoice')
async def invoice_pdf(request: Request, body: dict = Body(...)):
    """Render an invoice PDF with fpdf2 (was synchronous in the BFF).

    Accepts either a user's access token (the normal browser download) or
    the shared service key (internal callers with no browser session).
    """
    from si_common.auth import decode_token
    from si_common.config import get_settings
    settings = get_settings('workers')

    authorized = False
    header = request.headers.get('Authorization', '')
    if header.lower().startswith('bearer '):
        authorized = bool(decode_token(header[7:].strip(), 'workers'))
    if not authorized and request.headers.get('X-Service-Key') == settings.internal_api_key:
        authorized = True
    if not authorized:
        raise HTTPException(status_code=401, detail='Missing or invalid access token')

    invoice = body.get('invoice') or {}
    company = body.get('company')
    if not invoice:
        raise HTTPException(status_code=422, detail='invoice is required')
    try:
        buf = pdf.generate_invoice_pdf(invoice, company)
        content = buf.read()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'PDF generation failed: {exc}')
    return Response(content=content, media_type='application/pdf',
                    headers={'Content-Disposition': 'inline; filename="invoice.pdf"'})


@router.get('/admin/stats')
def admin_stats(_: Identity = Depends(require_admin)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    thirty_days_ago = now - timedelta(days=30)

    active_ids = set()
    for row in repos.events.coll.find(
            {'created_at': {'$gte': today_start}, 'user_id': {'$ne': None}},
            {'user_id': 1}):
        if row.get('user_id'):
            active_ids.add(str(row['user_id']))

    recent, _ = repos.events.find_all(1, 20, {})
    usage = list(repos.events.aggregate([
        {'$match': {'created_at': {'$gte': thirty_days_ago}}},
        {'$group': {'_id': {'$dateToString': {'format': '%Y-%m-%d',
                                               'date': '$created_at'}},
                    'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}},
    ]))
    return {
        'total_activities': repos.events.count(),
        'today_activities': repos.events.count({'created_at': {'$gte': today_start}}),
        'active_users': len(active_ids),
        'recent_events': [event_out(e) for e in recent],
        'db_usage_30d': [{'day': d['_id'], 'count': d['count']} for d in usage],
    }
