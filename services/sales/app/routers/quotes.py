"""Customer quotes: CRUD, send/validate workflow, numbering and totals.

The quote -> order -> auto-invoice conversion used to be orchestrated by the
web route; it now runs entirely inside this service (single database, atomic
from the caller's perspective).
"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException

from si_common.auth import Identity, make_require_company
from si_common.events import activity, emit_event
from si_common.ids import oid
from si_common.tenancy import scoped

from .. import orders as order_service
from .. import repos
from ..serialize import quote_out

logger = logging.getLogger(__name__)
router = APIRouter(tags=['customer-quotes'])

require_company = make_require_company('sales')


def _emit(identity, event_type, act=None, payload=None):
    emit_event(repos.quotes.db, event_type, source='sales',
               company_id=identity.company_id, actor_user_id=identity.user_id,
               activity=act, payload=payload)


def _filters(raw):
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {}


def _totals(payload):
    subtotal = sum(it['quantity'] * it['unit_price'] for it in payload['items'])
    discount = subtotal * payload['discount_percent'] / 100
    taxable = subtotal - discount
    payload['subtotal'] = subtotal
    payload['discount_amount'] = discount
    payload['tax_amount'] = taxable * payload['tax_percent'] / 100
    payload['total'] = taxable + payload['tax_amount']
    return payload


def _valid_until(value):
    if not value:
        return None
    if isinstance(value, str):
        return datetime.strptime(value, '%Y-%m-%d')
    return value


@router.get('')
def list_quotes(filters: str | None = None, page: int = 1, per_page: int = 20,
                identity: Identity = Depends(require_company)):
    docs, total = repos.quotes.find_all(page, per_page,
                                        scoped(identity, _filters(filters)))
    return {'items': [quote_out(d) for d in docs], 'total': total}


@router.get('/id/{quote_id}')
def get_quote(quote_id: str, identity: Identity = Depends(require_company)):
    doc = repos.quotes.find_by_id(quote_id, scoped(identity))
    if not doc:
        raise HTTPException(status_code=404, detail='Quote not found.')
    return quote_out(doc)


@router.post('')
def create_quote(body: dict = Body(...), identity: Identity = Depends(require_company)):
    payload = dict(body)
    count = repos.quotes.count(scoped(identity))
    payload['quote_number'] = f"Q{datetime.now().strftime('%d%m%y')}-{count + 1:02d}"
    payload['status'] = payload.get('status') or 'draft'
    payload['valid_until'] = _valid_until(payload.get('valid_until'))
    payload['company_id'] = oid(identity.company_id)
    payload['created_by'] = oid(identity.user_id)
    payload.setdefault('discount_percent', 0)
    payload.setdefault('tax_percent', 0)
    payload = _totals(payload)

    quote_id = repos.quotes.create(payload)
    _emit(identity, 'sales.quote.created',
          act=activity('quote', '', payload['quote_number'], 'created'),
          payload={'id': quote_id, 'quote_number': payload['quote_number']})
    return {'id': quote_id, 'quote_number': payload['quote_number']}


@router.patch('/{quote_id}')
def edit_quote(quote_id: str, body: dict = Body(...),
               identity: Identity = Depends(require_company)):
    if not repos.quotes.find_by_id(quote_id, scoped(identity)):
        raise HTTPException(status_code=404, detail='Quote not found.')
    payload = dict(body)
    payload.pop('quote_number', None)
    payload['valid_until'] = _valid_until(payload.get('valid_until'))
    payload.setdefault('tax_percent', 0)
    payload = _totals(payload)
    repos.quotes.update(quote_id, payload)
    return {'ok': True}


@router.post('/{quote_id}/send')
def send_quote(quote_id: str, identity: Identity = Depends(require_company)):
    doc = repos.quotes.find_by_id(quote_id, scoped(identity))
    if not doc:
        raise HTTPException(status_code=404, detail='Quote not found.')
    repos.quotes.update(quote_id, {'status': 'sent'})
    _emit(identity, 'sales.quote.sent',
          act=activity('quote', quote_id, doc.get('quote_number', ''), 'sent'),
          payload={'id': quote_id, 'quote_number': doc.get('quote_number', '')})
    return {'ok': True}


@router.post('/{quote_id}/validate')
def validate_quote(quote_id: str, identity: Identity = Depends(require_company)):
    """Convert an accepted quote into an order (and its auto-invoice)."""
    doc = repos.quotes.find_by_id(quote_id, scoped(identity))
    if not doc:
        raise HTTPException(status_code=404, detail='Quote not found.')

    order_payload = {
        'customer_name': doc.get('customer_name', ''),
        'contact_name': doc.get('contact_name', ''),
        'contact_email': doc.get('contact_email', ''),
        'customer_address': doc.get('customer_address', ''),
        'items': [{'sku': it.get('sku'), 'quantity': it.get('quantity'),
                   'unit_price': it.get('unit_price'),
                   'name': it.get('name', '')}
                  for it in doc.get('items', [])],
        'discount_percent': float(doc.get('discount_percent', 0)),
        'tax_percent': float(doc.get('tax_percent', 0)),
        'notes': f"From Quote {doc.get('quote_number', '')}",
        'status': 'confirmed',
    }
    order_id, order_number = order_service.create(order_payload, identity)

    repos.quotes.update(quote_id, {
        'status': 'accepted',
        'generated_order_id': oid(order_id),
        'generated_order_number': order_number,
    })

    _emit(identity, 'sales.quote.validated',
          act=activity('quote', quote_id, doc.get('quote_number', ''), 'validated'),
          payload={'id': quote_id, 'order_id': order_id,
                   'order_number': order_number})
    _emit(identity, 'sales.order.created',
          act=activity('order', order_id, order_number, 'created'),
          payload={'id': order_id, 'order_number': order_number})
    return {'order_id': order_id, 'order_number': order_number}


@router.delete('/{quote_id}')
def delete_quote(quote_id: str, identity: Identity = Depends(require_company)):
    doc = repos.quotes.find_by_id(quote_id, scoped(identity))
    if not doc:
        raise HTTPException(status_code=404, detail='Quote not found.')
    repos.quotes.delete(quote_id)
    _emit(identity, 'sales.quote.deleted',
          act=activity('quote', quote_id, doc.get('quote_number', ''), 'deleted'),
          payload={'id': quote_id, 'quote_number': doc.get('quote_number', '')})
    return {'ok': True}
