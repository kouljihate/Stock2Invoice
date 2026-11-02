"""procurement-service — procure-to-pay: suppliers, purchase orders, goods
receipts, supplier invoices, payments. Self-contained (no cross-service
calls in the P2P chain); publishes lifecycle events for the activity log."""

from si_common.service import create_service

from . import repos
from .routers import (dashboard, goods_receipts, payments, purchase_orders,
                      stats, supplier_invoices, suppliers)

app = create_service(
    'procurement',
    title='StockInvoice procurement service',
    binding_keys=(),   # publishes only; no consumer in this service
    indexes=repos.INDEXES,
    routers=(
        (suppliers.router, '/suppliers'),
        (purchase_orders.router, '/purchase-orders'),
        (goods_receipts.router, '/goods-receipts'),
        (supplier_invoices.router, '/supplier-invoices'),
        (payments.router, '/payments'),
        (dashboard.router, ''),
        (stats.router, ''),
    ),
)
