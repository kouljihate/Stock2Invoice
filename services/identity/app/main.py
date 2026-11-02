"""identity-service — users, companies, roles, credentials, session events."""

from si_common.service import create_service

from . import seed
from .routers import admin, auth, companies, roles, users

app = create_service(
    'identity',
    title='StockInvoice identity service',
    binding_keys=(),   # publishes only; no consumer in this service
    routers=(
        (auth.router, '/auth'),
        (users.router, '/users'),
        (companies.router, '/companies'),
        (roles.router, '/roles'),
        (admin.router, ''),
    ),
    on_startup=seed.bootstrap,
)
