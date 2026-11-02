"""Synchronous reads against inventory-service (product/SKU validation).

The monolith looked products up in-process when validating quotes, orders and
invoices; sales-service keeps the same *synchronous* semantics with an
internal REST call, so validation errors are byte-for-byte identical. Actual
stock deduction is asynchronous (RabbitMQ), fired only when an invoice
becomes paid.
"""

import logging

from si_common.http import ServiceCallError, call

logger = logging.getLogger(__name__)


def find_by_sku(sku, identity):
    """Product dict for ``sku`` in the caller's company, or None."""
    from urllib.parse import quote
    try:
        return call('inventory', f'/products/sku/{quote(sku, safe="")}',
                    identity=identity)
    except ServiceCallError as exc:
        if exc.status == 404:
            return None
        logger.error('inventory lookup failed for sku=%s: %s', sku, exc)
        raise


def product_list(identity, filters=None, unpaginated=False):
    """Company products for the edit forms (was ``find_all_unpaginated``)."""
    import json
    params = {}
    if filters:
        params['filters'] = json.dumps(filters, default=str)
    if unpaginated:
        params['per_page'] = 10000
    try:
        return call('inventory', '/products', params=params, identity=identity)
    except ServiceCallError as exc:
        logger.error('inventory product list failed: %s', exc)
        raise
