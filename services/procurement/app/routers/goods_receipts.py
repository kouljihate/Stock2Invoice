"""Goods receipts: CRUD + the receive workflow that closes the PO and
auto-generates the supplier invoice at PO prices."""

import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, HTTPException

from si_common.auth import Identity, make_require_company
from si_common.ids import oid
from si_common.tenancy import scoped

from .. import activity, repos
from ..serialize import gr_out

logger = logging.getLogger(__name__)
router = APIRouter(tags=['goods-receipts'])

require_company = make_require_company('procurement')


def _filters(raw):
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {}


@router.get('')
def list_receipts(filters: str | None = None, page: int = 1, per_page: int = 20,
                  identity: Identity = Depends(require_company)):
    docs, total = repos.goods_receipts.find_all(
        page, per_page, scoped(identity, _filters(filters)))
    items = []
    for doc in docs:
        row = gr_out(doc)
        po_id = row.get('po_id')
        if po_id:
            po = repos.purchase_orders.find_by_id(po_id, scoped(identity))
            row['po_status'] = po.get('status', '') if po else ''
        else:
            row['po_status'] = ''
        items.append(row)
    return {'items': items, 'total': total}


@router.get('/id/{gr_id}')
def get_receipt(gr_id: str, identity: Identity = Depends(require_company)):
    doc = repos.goods_receipts.find_by_id(gr_id, scoped(identity))
    if not doc:
        raise HTTPException(status_code=404, detail='Goods receipt not found.')
    return gr_out(doc)


@router.post('')
def create_receipt(body: dict = Body(...), identity: Identity = Depends(require_company)):
    payload = dict(body)
    count = repos.goods_receipts.count(scoped(identity))
    payload['receipt_number'] = f"GR-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
    payload['status'] = payload.get('status') or 'waiting'
    payload['company_id'] = oid(identity.company_id)
    payload['created_by'] = oid(identity.user_id)
    for key in ('po_id', 'supplier_id'):
        if payload.get(key):
            payload[key] = oid(payload[key])
    gr_id = repos.goods_receipts.create(payload)
    activity.crud_event('goods_receipt', identity, 'created', gr_id,
                        payload['receipt_number'])
    return {'id': gr_id, 'receipt_number': payload['receipt_number']}


@router.patch('/{gr_id}')
def edit_receipt(gr_id: str, body: dict = Body(...),
                 identity: Identity = Depends(require_company)):
    if not repos.goods_receipts.find_by_id(gr_id, scoped(identity)):
        raise HTTPException(status_code=404, detail='Goods receipt not found.')
    payload = dict(body)
    payload.pop('receipt_number', None)
    payload.pop('status', None)
    for key in ('po_id', 'supplier_id'):
        if payload.get(key):
            payload[key] = oid(payload[key])
    repos.goods_receipts.update(gr_id, payload)
    return {'ok': True}


@router.post('/{gr_id}/mark-received')
def mark_received(gr_id: str, identity: Identity = Depends(require_company)):
    """Close the PO + receipt and auto-create the supplier invoice."""
    gr = repos.goods_receipts.find_by_id(gr_id, scoped(identity))
    if not gr:
        raise HTTPException(status_code=404, detail='Goods receipt not found.')

    po_id = str(gr.get('po_id') or '')
    if not po_id:
        return {'result': 'no_po'}

    po = repos.purchase_orders.find_by_id(po_id, scoped(identity))
    if not po:
        raise HTTPException(status_code=404, detail='Linked purchase order not found.')

    repos.purchase_orders.update(po_id, {'status': 'received'})
    repos.goods_receipts.update(gr_id, {'status': 'received'})
    activity.crud_event('purchase_order', identity, 'received', po_id,
                        po.get('po_number', ''))

    po_items = {it['sku']: it for it in (po.get('items') or [])}
    si_items = []
    for it in (gr.get('items') or []):
        sku = it.get('sku', '')
        po_it = po_items.get(sku, {})
        si_items.append({
            'sku': sku,
            'name': it.get('name', po_it.get('name', '')),
            'quantity': int(it.get('quantity', 0)),
            'unit_price': float(po_it.get('unit_price', 0)),
        })

    count = repos.supplier_invoices.count(scoped(identity))
    inv_number = f"SI-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
    subtotal = sum(it['quantity'] * it['unit_price'] for it in si_items)
    discount_pct = float(po.get('discount_percent', 0))
    tax_pct = float(po.get('tax_percent', 0))
    discount = subtotal * discount_pct / 100
    taxable = subtotal - discount
    tax_amount = taxable * tax_pct / 100
    si_payload = {
        'invoice_number': inv_number,
        'supplier_id': oid(str(po.get('supplier_id') or '')),
        'supplier_name': po.get('supplier_name', ''),
        'po_id': oid(po_id),
        'po_number': po.get('po_number', ''),
        'invoice_date': datetime.now(timezone.utc),
        'due_date': datetime.now(timezone.utc) + timedelta(days=30),
        'items': si_items,
        'subtotal': subtotal,
        'discount_percent': discount_pct,
        'tax_percent': tax_pct,
        'discount_amount': discount,
        'tax_amount': tax_amount,
        'total': subtotal - discount + tax_amount,
        'notes': f"Auto-generated from goods receipt {gr.get('receipt_number', '')}",
        'status': 'draft',
        'company_id': oid(identity.company_id),
        'created_by': oid(identity.user_id),
    }
    si_id = repos.supplier_invoices.create(si_payload)
    activity.crud_event('supplier_invoice', identity, 'created', si_id,
                        inv_number)
    return {'result': 'received', 'receipt_number': gr.get('receipt_number', ''),
            'invoice_number': inv_number}


@router.delete('/{gr_id}')
def delete_receipt(gr_id: str, identity: Identity = Depends(require_company)):
    gr = repos.goods_receipts.find_by_id(gr_id, scoped(identity))
    if not gr:
        raise HTTPException(status_code=404, detail='Goods receipt not found.')
    repos.goods_receipts.delete(gr_id)
    activity.crud_event('goods_receipt', identity, 'deleted', gr_id,
                        gr.get('receipt_number', ''))
    return {'ok': True}
