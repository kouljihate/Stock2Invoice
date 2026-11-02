"""Repositories + index definitions owned by inventory-service."""

from si_common.crud import Repository
from si_common.db import ensure_indexes

products = Repository('inventory', 'products')
movements = Repository('inventory', 'stock_movements')

INDEXES = {
    'products': [
        ([('company_id', 1), ('sku', 1)], {'unique': True, 'name': 'uniq_products_company_sku'}),
        ([('company_id', 1), ('status', 1)], {'name': 'products_company_status'}),
        ([('company_id', 1), ('name', 1)], {'name': 'products_company_name'}),
    ],
    'stock_movements': [
        ([('company_id', 1), ('created_at', -1)], {'name': 'movements_company_created'}),
        ([('company_id', 1), ('sku', 1)], {'name': 'movements_company_sku'}),
    ],
}


def ensure_all():
    return ensure_indexes('inventory', INDEXES)
