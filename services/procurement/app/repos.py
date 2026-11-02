"""Repositories + index definitions owned by procurement-service."""

from si_common.crud import Repository
from si_common.db import ensure_indexes

suppliers = Repository('procurement', 'suppliers')
purchase_orders = Repository('procurement', 'purchase_orders')
goods_receipts = Repository('procurement', 'goods_receipts')
supplier_invoices = Repository('procurement', 'supplier_invoices')
payments = Repository('procurement', 'payments')

INDEXES = {
    'purchase_orders': [
        ([('company_id', 1), ('status', 1)], {'name': 'po_company_status'}),
    ],
    'supplier_invoices': [
        ([('company_id', 1), ('status', 1)], {'name': 'supplier_inv_company_status'}),
    ],
    'goods_receipts': [
        ([('company_id', 1), ('created_at', -1)], {'name': 'gr_company_created'}),
    ],
    'payments': [
        ([('company_id', 1), ('created_at', -1)], {'name': 'payments_company_created'}),
    ],
    'suppliers': [
        ([('company_id', 1)], {'name': 'suppliers_company'}),
    ],
}


def ensure_all():
    return ensure_indexes('procurement', INDEXES)
