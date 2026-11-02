"""Supplier invoices: create, approve (auto payment), invalidate, delete."""

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException

from si_common.auth import Identity, make_require_company
from si_common.ids import oid
from si_common.tenancy import scoped

from .. import activity, repos
from ..serialize import si_out

logger = logging.getLogger(__name__)
router = APIRouter(tags=['supplier-invoices'])

require_company = make_require_company('procurement')


def _filters(raw):
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {}


@router.get('')
def list_invoices(filters: str | None = None, page: int = 1, per_page: int = 20,
                  identity: Identity = Depends(require_company)):
    docs, total = repos.supplier_invoices.find_all(
        page, per_page, scoped(identity, _filters(filters)))
    return {'items': [si_out(d) for d in docs], 'total': total}


@router.get('/id/{inv_id}')
def get_invoice(inv_id: str, identity: Identity = Depends(require_company)):
    doc = repos.supplier_invoices.find_by_id(inv_id, scoped(identity))
    if not doc:
        raise HTTPException(status_code=404, detail='Invoice not found.')
    return si_out(doc)


@router.post('')
def create_invoice(body: dict = Body(...), identity: Identity = Depends(require_company)):
    payload = dict(body)
    count = repos.supplier_invoices.count(scoped(identity))
    payload['invoice_number'] = f"SI-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
    payload['invoice_date'] = datetime.now(timezone.utc)
    if payload.get('due_date'):
        due = payload['due_date']
        payload['due_date'] = (datetime.strptime(due, '%Y-%m-%d')
                               if isinstance(due, str) else due)
    payload['status'] = payload.get('status') or 'draft'
    payload['company_id'] = oid(identity.company_id)
    payload['created_by'] = oid(identity.user_id)
    for key in ('supplier_id', 'po_id'):
        if payload.get(key):
            payload[key] = oid(payload[key])
    payload.setdefault('discount_percent', 0)
    payload.setdefault('tax_percent', 0)

    subtotal = sum(it['quantity'] * it['unit_price'] for it in payload['items'])
    discount = subtotal * payload['discount_percent'] / 100
    taxable = subtotal - discount
    payload['subtotal'] = subtotal
    payload['discount_amount'] = discount
    payload['tax_amount'] = taxable * payload['tax_percent'] / 100
    payload['total'] = taxable + payload['tax_amount']

    inv_id = repos.supplier_invoices.create(payload)
    activity.crud_event('supplier_invoice', identity, 'created', inv_id,
                        payload['invoice_number'])
    return {'id': inv_id, 'invoice_number': payload['invoice_number']}


@router.post('/{inv_id}/validate')
def validate_invoice(inv_id: str, identity: Identity = Depends(require_company)):
    """Approve the invoice and open a pending payment for it."""
    inv = repos.supplier_invoices.find_by_id(inv_id, scoped(identity))
    if not inv:
        raise HTTPException(status_code=404, detail='Supplier invoice not found.')

    repos.supplier_invoices.update(inv_id, {'status': 'approved'})

    # The monolith numbered this PAY- series against the *global* payment
    # count (no tenant filter) — preserved verbatim.
    payment_number = (f"PAY-{datetime.now().strftime('%Y%m%d')}-"
                      f"{repos.payments.count() + 1:04d}")
    payment_data = {
        'payment_number': payment_number,
        'supplier_id': inv.get('supplier_id'),
        'supplier_name': inv.get('supplier_name', ''),
        'invoice_id': inv_id,
        'invoice_number': inv.get('invoice_number', ''),
        'amount': inv.get('total', 0),
        'payment_date': datetime.now(timezone.utc),
        'payment_method': 'bank_transfer',
        'reference': f"Payment for invoice {inv.get('invoice_number')}",
        'notes': (f"Auto-generated payment for validated supplier invoice "
                  f"{inv.get('invoice_number')}"),
        'status': 'pending',
        'company_id': inv.get('company_id'),
        'created_by': identity.user_id,
    }
    repos.payments.create(payment_data)

    activity.crud_event('supplier_invoice', identity, 'approved', inv_id,
                        inv.get('invoice_number', ''))
    return {'ok': True, 'payment_number': payment_number}


@router.post('/{inv_id}/invalidate')
def invalidate_invoice(inv_id: str, identity: Identity = Depends(require_company)):
    inv = repos.supplier_invoices.find_by_id(inv_id, scoped(identity))
    if not inv:
        raise HTTPException(status_code=404, detail='Supplier invoice not found.')
    repos.supplier_invoices.update(inv_id, {'status': 'draft'})
    activity.crud_event('supplier_invoice', identity, 'invalidated', inv_id,
                        inv.get('invoice_number', ''))
    return {'ok': True}


@router.delete('/{inv_id}')
def delete_invoice(inv_id: str, identity: Identity = Depends(require_company)):
    inv = repos.supplier_invoices.find_by_id(inv_id, scoped(identity))
    if not inv:
        raise HTTPException(status_code=404, detail='Supplier invoice not found.')
    repos.supplier_invoices.delete(inv_id)
    activity.crud_event('supplier_invoice', identity, 'deleted', inv_id,
                        inv.get('invoice_number', ''))
    return {'ok': True}
