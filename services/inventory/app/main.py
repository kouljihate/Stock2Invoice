"""inventory-service — products, stock, and the sales->stock deduction
consumer."""

from si_common.service import create_service

from . import consumer, repos
from .routers import admin, dashboard, movements, products

app = create_service(
    'inventory',
    title='StockInvoice inventory service',
    binding_keys=('sales.#',),
    consumer=consumer.handle,
    indexes=repos.INDEXES,
    routers=(
        (products.router, '/products'),
        (movements.router, '/movements'),
        (dashboard.router, ''),
        (admin.router, ''),
    ),
)
