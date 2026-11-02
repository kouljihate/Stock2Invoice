"""Customer invoice endpoints; business logic lives in ``app.invoices``."""

import json

from fastapi import APIRouter, Body, Depends, HTTPException

from si_common.auth import Identity, make_require_company
from si_common.events import activity, emit_event
from si_common.tenancy import scoped

from .. import invoices as service
from .. import repos
from ..serialize import invoice_out

router = APIRouter(tags=['invoices'])

require_company = make_require_company('sales')


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
    items, total = service.list(page, per_page, _filters(filters), identity)
    return {'items': items, 'total': total}


@router.get('/recent')
def recent_invoices(limit: int = 5, identity: Identity = Depends(require_company)):
    return {'items': service.get_recent(limit, identity)}


@router.get('/counts')
def invoice_counts(identity: Identity = Depends(require_company)):
    return service.get_counts(identity)


@router.get('/sales/month')
def month_sales(identity: Identity = Depends(require_company)):
    return {'total': service.get_month_sales(identity)}


@router.get('/sales/year')
def year_sales(identity: Identity = Depends(require_company)):
    return {'total': service.get_year_sales(identity)}


@router.get('/id/{invoice_id}')
def get_invoice(invoice_id: str, identity: Identity = Depends(require_company)):
    inv = service.get_by_id(invoice_id, identity)
    if not inv:
        raise HTTPException(status_code=404, detail='Invoice not found.')
    return inv


@router.post('/validate')
def validate_invoice(body: dict = Body(...),
                     identity: Identity = Depends(require_company)):
    data = body.get('data') or body
    return {'errors': service.validate(data, identity)}


@router.post('')
def create_invoice(body: dict = Body(...),
                   identity: Identity = Depends(require_company)):
    invoice_id, invoice_number = service.create(body, identity)
    return {'id': invoice_id, 'invoice_number': invoice_number}


@router.patch('/{invoice_id}')
def update_invoice(invoice_id: str, body: dict = Body(...),
                   identity: Identity = Depends(require_company)):
    result = service.update(invoice_id, body, identity)
    if result is None:
        raise HTTPException(status_code=404, detail='Invoice not found.')
    return {'ok': True}


@router.delete('/{invoice_id}')
def delete_invoice(invoice_id: str, identity: Identity = Depends(require_company)):
    doc = repos.invoices.find_by_id(invoice_id, scoped(identity))
    if not doc:
        raise HTTPException(status_code=404, detail='Invoice not found.')
    repos.invoices.delete(invoice_id)
    emit_event(repos.invoices.db, 'sales.invoice.deleted', source='sales',
               company_id=identity.company_id, actor_user_id=identity.user_id,
               activity=activity('invoice', invoice_id,
                                 doc.get('invoice_number', ''), 'deleted'),
               payload={'id': invoice_id,
                        'invoice_number': doc.get('invoice_number', '')})
    return {'ok': True}
