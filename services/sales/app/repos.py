"""Repositories + index definitions owned by sales-service."""

from si_common.crud import Repository
from si_common.db import ensure_indexes

customers = Repository('sales', 'customers')
quotes = Repository('sales', 'customer_quotes')
orders = Repository('sales', 'orders')
delivery_notes = Repository('sales', 'delivery_notes')
invoices = Repository('sales', 'invoices')

INDEXES = {
    'invoices': [
        ([('company_id', 1), ('status', 1)], {'name': 'invoices_company_status'}),
        ([('company_id', 1), ('created_at', -1)], {'name': 'invoices_company_created'}),
        ([('company_id', 1), ('invoice_number', 1)], {'name': 'invoices_company_number'}),
    ],
    'orders': [
        ([('company_id', 1), ('status', 1)], {'name': 'orders_company_status'}),
        ([('company_id', 1), ('created_at', -1)], {'name': 'orders_company_created'}),
    ],
    'customer_quotes': [
        ([('company_id', 1), ('status', 1)], {'name': 'quotes_company_status'}),
        ([('company_id', 1), ('created_at', -1)], {'name': 'quotes_company_created'}),
    ],
    'delivery_notes': [
        ([('company_id', 1), ('created_at', -1)], {'name': 'dn_company_created'}),
    ],
    'customers': [
        ([('company_id', 1)], {'name': 'customers_company'}),
    ],
}


def ensure_all():
    return ensure_indexes('sales', INDEXES)
