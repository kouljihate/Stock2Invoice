"""Purchase orders: CRUD, send workflow (auto-generates the goods receipt)."""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException

from si_common.auth import Identity, make_require_company
from si_common.ids import oid
from si_common.tenancy import scoped

from .. import activity, repos
from ..serialize import po_out

logger = logging.getLogger(__name__)
router = APIRouter(tags=['purchase-orders'])

require_company = make_require_company('procurement')


def _filters(raw):
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {}


@router.get('')
def list_purchase_orders(filters: str | None = None, page: int = 1,
                         per_page: int = 20,
                         identity: Identity = Depends(require_company)):
    docs, total = repos.purchase_orders.find_all(
        page, per_page, scoped(identity, _filters(filters)))
    return {'items': [po_out(d) for d in docs], 'total': total}


@router.get('/id/{po_id}')
def get_purchase_order(po_id: str, identity: Identity = Depends(require_company)):
    doc = repos.purchase_orders.find_by_id(po_id, scoped(identity))
    if not doc:
        raise HTTPException(status_code=404, detail='Purchase order not found.')
    return po_out(doc)


@router.post('')
def create_purchase_order(body: dict = Body(...),
                          identity: Identity = Depends(require_company)):
    payload = dict(body)
    count = repos.purchase_orders.count(scoped(identity))
    payload['po_number'] = f"PO-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
    payload['status'] = payload.get('status') or 'draft'
    payload['company_id'] = oid(identity.company_id)
    payload['created_by'] = oid(identity.user_id)
    if payload.get('supplier_id'):
        payload['supplier_id'] = oid(payload['supplier_id'])
    payload.setdefault('discount_percent', 0)
    payload.setdefault('tax_percent', 0)

    subtotal = sum(it['quantity'] * it['unit_price'] for it in payload['items'])
    discount = subtotal * payload['discount_percent'] / 100
    taxable = subtotal - discount
    payload['subtotal'] = subtotal
    payload['discount_amount'] = discount
    payload['tax_amount'] = taxable * payload['tax_percent'] / 100
    payload['total'] = taxable + payload['tax_amount']

    po_id = repos.purchase_orders.create(payload)
    activity.crud_event('purchase_order', identity, 'created', po_id,
                        payload['po_number'])
    return {'id': po_id, 'po_number': payload['po_number']}


@router.post('/{po_id}/send')
def send_purchase_order(po_id: str, identity: Identity = Depends(require_company)):
    """Mark the PO sent and auto-create its waiting goods receipt."""
    po = repos.purchase_orders.find_by_id(po_id, scoped(identity))
    if not po:
        raise HTTPException(status_code=404, detail='Purchase order not found.')
    repos.purchase_orders.update(po_id, {'status': 'sent'})
    activity.crud_event('purchase_order', identity, 'sent', po_id,
                        po.get('po_number', ''))

    gr_count = repos.goods_receipts.count(scoped(identity))
    receipt_number = f"GR-{datetime.now().strftime('%Y%m%d')}-{gr_count + 1:04d}"
    gr_payload = {
        'receipt_number': receipt_number,
        'po_id': oid(po_id),
        'po_number': po.get('po_number', ''),
        'supplier_id': po.get('supplier_id'),
        'supplier_name': po.get('supplier_name', ''),
        'items': [{'sku': it.get('sku', ''), 'quantity': it.get('quantity', 0),
                   'name': it.get('name', '')} for it in po.get('items', [])],
        'notes': '',
        'status': 'waiting',
        'company_id': oid(identity.company_id),
        'created_by': oid(identity.user_id),
    }
    repos.goods_receipts.create(gr_payload)
    return {'ok': True, 'receipt_number': receipt_number}


@router.delete('/{po_id}')
def delete_purchase_order(po_id: str, identity: Identity = Depends(require_company)):
    po = repos.purchase_orders.find_by_id(po_id, scoped(identity))
    if not po:
        raise HTTPException(status_code=404, detail='Purchase order not found.')
    repos.purchase_orders.delete(po_id)
    activity.crud_event('purchase_order', identity, 'deleted', po_id,
                        po.get('po_number', ''))
    return {'ok': True}
