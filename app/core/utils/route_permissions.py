"""Central, auditable endpoint -> permission map.

Enforced exactly once per request by the ``before_request`` hook installed in
the app factory, so a new route cannot silently ship unprotected: every
endpoint either resolves to a permission here or is explicitly listed as
unrestricted.

* ``BLUEPRINT_MODULES`` names the permission module a blueprint operates on.
* The action verb inside the endpoint name selects the operation
  (``create`` / ``edit`` / ``delete`` / ``send`` / ``validate`` / ``view``).
* ``ENDPOINT_PERMISSIONS`` overrides the derived value for endpoints whose
  name does not describe what they do.

Endpoints absent from both maps are not permission-checked. That covers the
auth blueprints, the dashboards, the eShop module (out of scope) and the admin
panel, which is guarded by ``super_admin_required`` on every one of its views.
"""

# blueprint name -> permission module
BLUEPRINT_MODULES = {
    'web_stock': 'product',
    'mobile_stock': 'product',
    'web_invoices': 'invoice',
    'mobile_invoices': 'invoice',
    'web_orders': 'order',
    'mobile_orders': 'order',
    'web_customers': 'customer',
    'web_customer_quotes': 'quote',
    'web_delivery_notes': 'delivery_note',
    'web_suppliers': 'supplier',
    'web_purchase_orders': 'purchase_order',
    'web_goods_receipt': 'goods_receipt',
    'web_supplier_invoices': 'supplier_invoice',
    'web_payments': 'payment',
    'web_users': 'user',
    'web_events': 'general.activities',
}

# endpoint -> required permission (wins over the derived value)
ENDPOINT_PERMISSIONS = {
    # Activity log is a cross-cutting read, not a module view
    'web_events.list_events': 'general.activities',
    # Creating a customer inline from a quote/order form
    'web_customer_quotes.ajax_create_customer': 'customer.create',
    # User administration is a management operation, not a CRUD verb
    'web_users.create_user': 'user.manage',
    'web_users.set_role': 'user.manage',
    # Invoice deletion is destructive rather than an ordinary edit
    'web_invoices.delete_invoice': 'invoice.delete',
    'web_orders.delete_order': 'order.delete',
}

# verb markers, longest/most specific first
_CREATE_MARKERS = ('create', 'bulk_upload')
_EDIT_MARKERS = ('edit', 'update', 'set_role', 'reset_password', 'mark_')
_SEND_MARKERS = ('send',)
_VALIDATE_MARKERS = ('validate', 'invalidate')


def _operation(func_name):
    name = func_name.lower()
    if 'delete' in name:
        return 'delete'
    if any(m in name for m in _CREATE_MARKERS):
        return 'create'
    if any(m in name for m in _SEND_MARKERS):
        return 'send'
    if any(m in name for m in _VALIDATE_MARKERS):
        return 'validate'
    if any(m in name for m in _EDIT_MARKERS):
        return 'edit'
    return 'view'


def permission_for(endpoint):
    """Return the permission string required for ``endpoint``, or None."""
    if not endpoint:
        return None
    if endpoint in ENDPOINT_PERMISSIONS:
        return ENDPOINT_PERMISSIONS[endpoint]
    blueprint, _, func = endpoint.partition('.')
    module = BLUEPRINT_MODULES.get(blueprint)
    if not module:
        return None
    return f'{module}.{_operation(func)}'


# Blueprints whose data belongs to a tenant. An authenticated account that is
# not linked to a company is refused outright, so no view in these blueprints
# can ever be reached unscoped.
#
# Deliberately absent: the auth blueprints, the dashboards (they render an
# empty state for company-less accounts), web_users (it already special-cases
# the platform admin), the admin panel (super_admin_required) and the eShop
# module (public catalogue, out of scope).
TENANT_SCOPED_BLUEPRINTS = frozenset({
    'web_stock', 'web_invoices', 'web_orders', 'web_customers',
    'web_customer_quotes', 'web_delivery_notes', 'web_suppliers',
    'web_purchase_orders', 'web_goods_receipt', 'web_supplier_invoices',
    'web_payments', 'web_events',
    'mobile_stock', 'mobile_invoices', 'mobile_orders',
})
