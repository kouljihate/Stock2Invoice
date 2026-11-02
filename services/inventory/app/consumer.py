"""RabbitMQ consumer: sales events that move stock.

The monolith deducted stock inline when an order was confirmed, when an
invoice was created as ``paid``, and when an invoice later transitioned to
``paid``. Those three flows now arrive as events; each deduction keeps its
original reference string, and failure is still best-effort (logged, never
poisoning the workflow).
"""

import logging

from . import service

logger = logging.getLogger(__name__)


def handle(event: dict):
    event_type = event.get('type', '')
    payload = event.get('payload') or {}
    company_id = event.get('company_id')
    actor = (event.get('actor') or {}).get('user_id')
    if not company_id:
        logger.warning('Ignoring %s without company scope', event_type)
        return

    items = payload.get('items') or []

    # Note: order *confirmation* deliberately does NOT deduct. The monolith's
    # confirmation path crashed before its deduction loop ran (undefined
    # ``OrderModel``), so stock only ever moved when an invoice became paid —
    # and moving it in both places would double-deduct. Preserved as-is.
    if event_type == 'sales.invoice.created' and payload.get('status') == 'paid':
        _deduct_all(items, company_id, actor,
                    f"Invoice {payload.get('invoice_number', '')}")
    elif (event_type == 'sales.invoice.status_changed'
          and payload.get('to') == 'paid'
          and payload.get('from') != 'paid'):
        _deduct_all(items, company_id, actor,
                    f"Invoice {payload.get('invoice_number', '')} confirmed")


def _deduct_all(items, company_id, user_id, reference):
    for item in items:
        sku = (item.get('sku') or '').strip()
        if not sku:
            continue
        try:
            qty = int(item.get('quantity', 0))
        except (TypeError, ValueError):
            continue
        if qty <= 0:
            continue
        if not service.deduct_stock(sku, qty, company_id,
                                    reference=reference, user_id=user_id):
            logger.error('Stock deduction failed for SKU=%s (%s)', sku, reference)
