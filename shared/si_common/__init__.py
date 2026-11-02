"""Shared kernel imported by every StockInvoice service (and the BFF).

Modules here are deliberately dependency-light and side-effect free at import
time so that unit tests can import them without a running broker or database.
"""

__all__ = [
    'config', 'rbac', 'tenancy', 'ids', 'db', 'auth', 'crud',
    'events', 'messaging', 'validators', 'http', 'service',
]
