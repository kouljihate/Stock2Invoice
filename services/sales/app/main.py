"""sales-service — quote-to-cash: customers, quotes, orders, delivery
notes, invoices. Owns the Q2C chain in one database so the quote -> order ->
invoice conversion stays synchronous; publishes the events that move stock."""

from si_common.service import create_service

from . import repos
from .routers import (customers, dashboard, delivery_notes, invoices, orders,
                      quotes, stats)

app = create_service(
    'sales',
    title='StockInvoice sales service',
    binding_keys=(),   # publishes only; no consumer in this service
    indexes=repos.INDEXES,
    routers=(
        (customers.router, '/customers'),
        (quotes.router, '/quotes'),
        (orders.router, '/orders'),
        (delivery_notes.router, '/delivery-notes'),
        (invoices.router, '/invoices'),
        (dashboard.router, ''),
        (stats.router, ''),
    ),
)
