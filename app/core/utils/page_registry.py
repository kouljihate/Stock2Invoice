"""UI page registry — a stable identity card for every screen in the app.

Each route gets a human page ID of the form ``<module>.<sequence>``. The
login screen, for example, is ``0.0``. The ID is rendered in a small badge
next to the version badge and opens a dialog describing the page: ID, name,
module, description, route, endpoint, template file, handler file and the
access level required to reach it.

The registry is built once at application start from ``app.url_map`` so a
badge is never missing or stale: every registered rule is present, including
actions (POST-only endpoints) that redirect and therefore never paint a badge
of their own.
"""

from flask import request

# Module numbers give the ID its hierarchy: 0.0 = first screen of module 0.
MODULES = {
    0: 'Authentication',
    1: 'Dashboard & Onboarding',
    2: 'Customers',
    3: 'Suppliers',
    4: 'Products & Stock',
    5: 'Quotes',
    6: 'Orders',
    7: 'Delivery Notes',
    8: 'Customer Invoices',
    9: 'Purchase Orders',
    10: 'Goods Receipt',
    11: 'Supplier Invoices',
    12: 'Payments',
    13: 'Users',
    14: 'Activity Log',
    15: 'Admin Platform',
    16: 'EShop',
    17: 'Mobile App',
    18: 'System',
}

# endpoint -> (module, sequence, name, description, template, access)
#
# ``template`` is relative to app/templates and may be empty for endpoints
# that only redirect, download a file or answer JSON.
PUBLIC = 'Public'
SIGNED_IN = 'Signed-in'
ADMIN_ONLY = 'Admin only'

PAGES = {
    # ---------------------------------------------------------------- 0 Auth
    'web_auth.login': (0, 0, 'Login',
                       'Email and password sign-in. The Reset Password tab lives on the same page.',
                       'auth/login.html', PUBLIC),
    'web_auth.register': (0, 1, 'Register',
                          'Self-service account registration, shown only when public registration is enabled.',
                          'auth/register.html', PUBLIC),
    'web_auth.forgot_password': (0, 2, 'Reset Password',
                                 'Password-reset request. A POST re-renders Login with the Reset tab active.',
                                 'auth/login.html', PUBLIC),
    'web_auth.logout': (0, 3, 'Logout',
                        'Clears the access cookie and returns to the login screen.',
                        '', SIGNED_IN),
    'mobile_auth.login': (0, 4, 'Mobile Login',
                          'Compact sign-in screen used by the mobile blueprint.',
                          'auth/login.html', PUBLIC),
    'mobile_auth.register': (0, 5, 'Mobile Register',
                             'Compact registration screen used by the mobile blueprint.',
                             'auth/register.html', PUBLIC),
    'mobile_auth.forgot_password': (0, 6, 'Mobile Reset Password',
                                    'Mobile password-reset request page.',
                                    'auth/forgot_password.html', PUBLIC),
    'mobile_auth.logout': (0, 7, 'Mobile Logout',
                           'Ends the mobile session and clears the access cookie.',
                           '', SIGNED_IN),

    # --------------------------------------------- 1 Dashboard & Onboarding
    'index': (1, 0, 'Root Entry',
              'Sends a signed-in visitor to the dashboard and everyone else to Login.',
              '', PUBLIC),
    'web_dashboard.index': (1, 1, 'Dashboard',
                            'KPI cards, charts and recent activity for the acting company.',
                            'dashboard/index.html', SIGNED_IN),
    'web_profile.setup': (1, 2, 'Company Setup Wizard',
                          'First-login wizard that registers the PME company and opens its private data space.',
                          'profile/setup.html', SIGNED_IN),
    'web_profile.edit': (1, 4, 'Edit Profile',
                         'The signed-in user maintains his own name and phone number.',
                         'profile/edit.html', SIGNED_IN),
    'mobile_dashboard.index': (1, 3, 'Mobile Dashboard',
                               'Compact KPI overview for the mobile blueprint.',
                               'dashboard/index.html', SIGNED_IN),

    # ----------------------------------------------------------- 2 Customers
    'web_customers.list_customers': (2, 0, 'Customers',
                                     'Searchable customer list with contact details and outstanding balances.',
                                     'customers/list.html', SIGNED_IN),
    'web_customers.create_customer': (2, 1, 'New Customer',
                                      'Creates a customer record for the acting company.',
                                      'customers/form.html', SIGNED_IN),
    'web_customers.edit_customer': (2, 2, 'Edit Customer',
                                    'Updates an existing customer record.',
                                    'customers/form.html', SIGNED_IN),
    'web_customers.delete_customer': (2, 3, 'Delete Customer',
                                      'Removes a customer. POST only; redirects back to the list.',
                                      '', SIGNED_IN),
    'web_customers.bulk_upload': (2, 4, 'Import Customers',
                                  'CSV bulk import of customer records.',
                                  'customers/bulk_upload.html', SIGNED_IN),

    # ----------------------------------------------------------- 3 Suppliers
    'web_suppliers.list_suppliers': (3, 0, 'Suppliers',
                                     'Supplier list with contact details and payable totals.',
                                     'suppliers/list.html', SIGNED_IN),
    'web_suppliers.create_supplier': (3, 1, 'New Supplier',
                                      'Creates a supplier record for the acting company.',
                                      'suppliers/form.html', SIGNED_IN),
    'web_suppliers.edit_supplier': (3, 2, 'Edit Supplier',
                                    'Updates an existing supplier record.',
                                    'suppliers/form.html', SIGNED_IN),
    'web_suppliers.delete_supplier': (3, 3, 'Delete Supplier',
                                      'Removes a supplier. POST only; redirects back to the list.',
                                      '', SIGNED_IN),
    'web_suppliers.bulk_upload': (3, 4, 'Import Suppliers',
                                  'CSV bulk import of supplier records.',
                                  'suppliers/bulk_upload.html', SIGNED_IN),

    # ---------------------------------------------------- 4 Products & Stock
    'web_stock.list_products': (4, 0, 'Products',
                                'Stock list with quantities, prices and low-stock alerts.',
                                'stock/list.html', SIGNED_IN),
    'web_stock.create_product': (4, 1, 'New Product',
                                 'Creates a product with SKU, price and opening stock.',
                                 'stock/edit.html', SIGNED_IN),
    'web_stock.edit_product': (4, 2, 'Edit Product',
                               'Updates product details and stock levels.',
                               'stock/edit.html', SIGNED_IN),
    'web_stock.view_product': (4, 3, 'Product Detail',
                               'Read-only product view with its stock movement history.',
                               'stock/detail.html', SIGNED_IN),
    'web_stock.delete_product': (4, 4, 'Delete Product',
                                 'Removes a product. POST only; redirects back to the list.',
                                 '', SIGNED_IN),
    'web_stock.bulk_upload': (4, 5, 'Import Products',
                              'CSV bulk import of products and opening quantities.',
                              'stock/bulk_upload.html', SIGNED_IN),
    'web_stock.api_lookup': (4, 6, 'Product Lookup API',
                             'JSON lookup used by the order and invoice line editors.',
                             '', SIGNED_IN),

    # -------------------------------------------------------------- 5 Quotes
    'web_customer_quotes.list_quotes': (5, 0, 'Quotes',
                                        'Customer quote list with status and total value.',
                                        'customer_quotes/list.html', SIGNED_IN),
    'web_customer_quotes.create_quote': (5, 1, 'New Quote',
                                         'Builds a customer quote with priced lines.',
                                         'customer_quotes/form.html', SIGNED_IN),
    'web_customer_quotes.edit_quote': (5, 2, 'Edit Quote',
                                       'Updates an existing customer quote.',
                                       'customer_quotes/form.html', SIGNED_IN),
    'web_customer_quotes.view_quote': (5, 3, 'Quote Detail',
                                       'Read-only quote with its lines and workflow actions.',
                                       'customer_quotes/detail.html', SIGNED_IN),
    'web_customer_quotes.send_quote': (5, 4, 'Send Quote',
                                       'Marks the quote as sent. POST only.',
                                       '', SIGNED_IN),
    'web_customer_quotes.validate_quote': (5, 5, 'Validate Quote',
                                           'Accepts the quote and unlocks conversion to an order. POST only.',
                                           '', SIGNED_IN),
    'web_customer_quotes.delete_quote': (5, 6, 'Delete Quote',
                                         'Removes a quote. POST only.',
                                         '', SIGNED_IN),
    'web_customer_quotes.ajax_create_customer': (5, 7, 'Quick-add Customer (AJAX)',
                                                 'Creates a customer from inside the quote form without leaving it. POST JSON only.',
                                                 '', SIGNED_IN),

    # -------------------------------------------------------------- 6 Orders
    'web_orders.list_orders': (6, 0, 'Orders',
                               'Sales order list with status and totals.',
                               'orders/list.html', SIGNED_IN),
    'web_orders.create_order': (6, 1, 'New Order',
                                'Creates a sales order with priced lines.',
                                'orders/edit.html', SIGNED_IN),
    'web_orders.view_order': (6, 2, 'Order Detail',
                              'Read-only order with its lines and workflow actions.',
                              'orders/detail.html', SIGNED_IN),
    'web_orders.update_status': (6, 3, 'Update Order Status',
                                 'Moves an order through its workflow. POST only.',
                                 '', SIGNED_IN),
    'web_orders.download_pdf': (6, 4, 'Order PDF',
                                'Printable order document.',
                                'orders/printable.html', SIGNED_IN),
    'web_orders.delete_order': (6, 5, 'Delete Order',
                                'Removes an order. POST only.',
                                '', SIGNED_IN),

    # ------------------------------------------------------ 7 Delivery Notes
    'web_delivery_notes.list_delivery_notes': (7, 0, 'Delivery Notes',
                                               'Delivery note list linked to their orders.',
                                               'delivery_notes/list.html', SIGNED_IN),
    'web_delivery_notes.create_delivery_note': (7, 1, 'New Delivery Note',
                                                'Creates a delivery note from an existing order.',
                                                'delivery_notes/form.html', SIGNED_IN),
    'web_delivery_notes.delete_delivery_note': (7, 2, 'Delete Delivery Note',
                                                'Removes a delivery note. POST only.',
                                                '', SIGNED_IN),

    # ---------------------------------------------------- 8 Customer Invoices
    'web_invoices.list_invoices': (8, 0, 'Invoices',
                                   'Customer invoice list with status and outstanding balance.',
                                   'invoices/list.html', SIGNED_IN),
    'web_invoices.create_invoice': (8, 1, 'New Invoice',
                                    'Creates a customer invoice with priced lines.',
                                    'invoices/edit.html', SIGNED_IN),
    'web_invoices.view_invoice': (8, 2, 'Invoice Detail',
                                  'Read-only invoice with its lines and status actions.',
                                  'invoices/detail.html', SIGNED_IN),
    'web_invoices.print_invoice': (8, 3, 'Print Invoice',
                                   'Print layout of a customer invoice.',
                                   'invoices/print.html', SIGNED_IN),
    'web_invoices.download_pdf': (8, 4, 'Invoice PDF',
                                  'Server-rendered PDF with the company branding.',
                                  '', SIGNED_IN),
    'web_invoices.update_status': (8, 5, 'Update Invoice Status',
                                   'Marks an invoice as sent, paid or cancelled. POST only.',
                                   '', SIGNED_IN),
    'web_invoices.delete_invoice': (8, 6, 'Delete Invoice',
                                    'Removes an invoice. POST only.',
                                    '', SIGNED_IN),

    # ----------------------------------------------------- 9 Purchase Orders
    'web_purchase_orders.list_orders': (9, 0, 'Purchase Orders',
                                        'Supplier purchase order list with status and totals.',
                                        'purchase_orders/list.html', SIGNED_IN),
    'web_purchase_orders.create_order': (9, 1, 'New Purchase Order',
                                         'Creates a purchase order for a supplier.',
                                         'purchase_orders/form.html', SIGNED_IN),
    'web_purchase_orders.view_order': (9, 2, 'Purchase Order Detail',
                                       'Read-only purchase order with its lines and actions.',
                                       'purchase_orders/detail.html', SIGNED_IN),
    'web_purchase_orders.send_order': (9, 3, 'Send Purchase Order',
                                       'Marks the purchase order as sent. POST only.',
                                       '', SIGNED_IN),
    'web_purchase_orders.delete_order': (9, 4, 'Delete Purchase Order',
                                         'Removes a purchase order. POST only.',
                                         '', SIGNED_IN),

    # -------------------------------------------------------- 10 Goods Receipt
    'web_goods_receipt.list_receipts': (10, 0, 'Goods Receipts',
                                        'Receipts recorded against purchase orders.',
                                        'goods_receipt/list.html', SIGNED_IN),
    'web_goods_receipt.create_receipt': (10, 1, 'New Goods Receipt',
                                         'Records delivered quantities for a purchase order.',
                                         'goods_receipt/form.html', SIGNED_IN),
    'web_goods_receipt.edit_receipt': (10, 2, 'Edit Goods Receipt',
                                       'Corrects a recorded goods receipt.',
                                       'goods_receipt/form.html', SIGNED_IN),
    'web_goods_receipt.mark_po_received': (10, 3, 'Mark PO Received',
                                           'Flags the parent purchase order as fully received. POST only.',
                                           '', SIGNED_IN),
    'web_goods_receipt.delete_receipt': (10, 4, 'Delete Goods Receipt',
                                         'Removes a goods receipt. POST only.',
                                         '', SIGNED_IN),

    # ---------------------------------------------------- 11 Supplier Invoices
    'web_supplier_invoices.list_invoices': (11, 0, 'Supplier Invoices',
                                            'Supplier invoice list with validation state.',
                                            'supplier_invoices/list.html', SIGNED_IN),
    'web_supplier_invoices.create_invoice': (11, 1, 'New Supplier Invoice',
                                             'Records a supplier invoice against a receipt.',
                                             'supplier_invoices/form.html', SIGNED_IN),
    'web_supplier_invoices.view_invoice': (11, 2, 'Supplier Invoice Detail',
                                           'Read-only supplier invoice with its validation actions.',
                                           'supplier_invoices/detail.html', SIGNED_IN),
    'web_supplier_invoices.validate_invoice': (11, 3, 'Validate Supplier Invoice',
                                               'Approves a supplier invoice for payment. POST only.',
                                               '', SIGNED_IN),
    'web_supplier_invoices.invalidate_invoice': (11, 4, 'Invalidate Supplier Invoice',
                                                 'Sends a supplier invoice back for correction. POST only.',
                                                 '', SIGNED_IN),
    'web_supplier_invoices.delete_invoice': (11, 5, 'Delete Supplier Invoice',
                                             'Removes a supplier invoice. POST only.',
                                             '', SIGNED_IN),

    # ------------------------------------------------------------ 12 Payments
    'web_payments.list_payments': (12, 0, 'Payments',
                                   'Payment list with direction, method and amount.',
                                   'payments/list.html', SIGNED_IN),
    'web_payments.create_payment': (12, 1, 'New Payment',
                                    'Records an incoming or outgoing payment.',
                                    'payments/form.html', SIGNED_IN),

    # --------------------------------------------------------------- 13 Users
    'web_users.list_users': (13, 0, 'Company Users',
                             'Users of the acting company and their roles.',
                             'web/users/list.html', SIGNED_IN),
    'web_users.create_user': (13, 1, 'Create Company User',
                              'Adds a user to the acting company. POST only.',
                              '', SIGNED_IN),
    'web_users.set_role': (13, 2, 'Set User Role',
                           'Changes a company user role. POST only.',
                           '', SIGNED_IN),

    # -------------------------------------------------------- 14 Activity Log
    'web_events.list_events': (14, 0, 'Activity Log',
                               'Chronological audit trail of logins and business events for the company.',
                               'events/list.html', SIGNED_IN),

    # -------------------------------------------------------- 15 Admin Platform
    'admin.index': (15, 0, 'Admin Dashboard',
                    'Platform overview: companies, users, data volumes and the RabbitMQ monitor.',
                    'admin/index.html', ADMIN_ONLY),
    'admin.companies': (15, 1, 'All Companies',
                        'Every tenant company with per-company user, product, order and invoice counts.',
                        'admin/companies.html', ADMIN_ONLY),
    'admin.company_detail': (15, 2, 'Company Detail',
                             'One company: its users, products, orders and invoices.',
                             'admin/company_detail.html', ADMIN_ONLY),
    'admin.company_users': (15, 3, 'Company Users (Admin)',
                            'Users belonging to one company, seen from the platform admin side.',
                            'admin/company_users.html', ADMIN_ONLY),
    'admin.create_company': (15, 4, 'New Company',
                             'Creates a company together with its first manager account.',
                             'admin/create_company.html', ADMIN_ONLY),
    'admin.edit_company': (15, 5, 'Edit Company',
                           'Updates company identity, legal IDs and the invoice template.',
                           'admin/edit_company.html', ADMIN_ONLY),
    'admin.delete_company': (15, 6, 'Delete Company',
                             'Removes a company. POST only.',
                             '', ADMIN_ONLY),
    'admin.add_user': (15, 7, 'Add User to Company',
                       'Creates a user inside an existing company with chosen roles.',
                       'admin/create_user.html', ADMIN_ONLY),
    'admin.list_users': (15, 8, 'All Users',
                         'Every platform user, searchable, with their company.',
                         'admin/users.html', ADMIN_ONLY),
    'admin.create_pme_admin': (15, 9, 'Create PME-Admin',
                               'Creates a PME-Admin with no company; the first login collects the company.',
                               'admin/create_pme_admin.html', ADMIN_ONLY),
    'admin.edit_user': (15, 10, 'Edit User (Admin)',
                        'Updates a user identity and role set from the admin side.',
                        'admin/edit_user.html', ADMIN_ONLY),
    'admin.reset_password': (15, 11, 'Reset User Password (Admin)',
                             'Sets a new password for a non-admin user. POST only.',
                             '', ADMIN_ONLY),
    'admin.set_user_role': (15, 12, 'Set User Role (Admin)',
                            'Maps a user between the Customer and PME-Admin profiles. POST only.',
                            '', ADMIN_ONLY),
    'admin.delete_user': (15, 13, 'Delete User (Admin)',
                          'Removes a non-admin user. POST only.',
                          '', ADMIN_ONLY),

    # --------------------------------------------------------------- 16 EShop
    'eshop.index': (16, 0, 'EShop Catalog',
                    'Public product catalog for the storefront.',
                    'eshop/index.html', PUBLIC),
    'eshop.product_item': (16, 1, 'EShop Product',
                           'Public product page with pricing and availability.',
                           'eshop/product.html', PUBLIC),
    'eshop.admin': (16, 2, 'EShop Admin',
                    'Shop-side order management panel.',
                    'eshop/admin.html', SIGNED_IN),

    # ----------------------------------------------------------- 17 Mobile App
    'mobile_stock.list_products': (17, 0, 'Mobile Products',
                                   'Mobile stock list.',
                                   'stock/list.html', SIGNED_IN),
    'mobile_stock.create_product': (17, 1, 'Mobile New Product',
                                    'Mobile product creation form.',
                                    'stock/edit.html', SIGNED_IN),
    'mobile_stock.edit_product': (17, 2, 'Mobile Edit Product',
                                  'Mobile product edit form.',
                                  'stock/edit.html', SIGNED_IN),
    'mobile_stock.view_product': (17, 3, 'Mobile Product Detail',
                                  'Mobile read-only product view.',
                                  'stock/detail.html', SIGNED_IN),
    'mobile_stock.delete_product': (17, 4, 'Mobile Delete Product',
                                    'Removes a product from the mobile blueprint. POST only.',
                                    '', SIGNED_IN),
    'mobile_orders.list_orders': (17, 5, 'Mobile Orders',
                                  'Mobile sales order list.',
                                  'orders/list.html', SIGNED_IN),
    'mobile_orders.create_order': (17, 6, 'Mobile New Order',
                                   'Mobile sales order creation.',
                                   'orders/edit.html', SIGNED_IN),
    'mobile_orders.view_order': (17, 7, 'Mobile Order Detail',
                                 'Mobile read-only order view.',
                                 'orders/detail.html', SIGNED_IN),
    'mobile_orders.update_status': (17, 8, 'Mobile Update Order Status',
                                    'Moves an order through its workflow from mobile. POST only.',
                                    '', SIGNED_IN),
    'mobile_orders.download_pdf': (17, 9, 'Mobile Order PDF',
                                   'Printable order document from mobile.',
                                   'orders/printable.html', SIGNED_IN),
    'mobile_invoices.list_invoices': (17, 10, 'Mobile Invoices',
                                      'Mobile customer invoice list.',
                                      'invoices/list.html', SIGNED_IN),
    'mobile_invoices.create_invoice': (17, 11, 'Mobile New Invoice',
                                       'Mobile customer invoice creation.',
                                       'invoices/edit.html', SIGNED_IN),
    'mobile_invoices.view_invoice': (17, 12, 'Mobile Invoice Detail',
                                     'Mobile read-only invoice view.',
                                     'invoices/detail.html', SIGNED_IN),
    'mobile_invoices.update_status': (17, 13, 'Mobile Update Invoice Status',
                                      'Marks an invoice sent, paid or cancelled from mobile. POST only.',
                                      '', SIGNED_IN),
    'mobile_invoices.download_pdf': (17, 14, 'Mobile Invoice PDF',
                                     'Server-rendered invoice PDF from mobile.',
                                     '', SIGNED_IN),

    # ------------------------------------------------------------ 18 System
    'health': (18, 0, 'Health Check',
               'JSON liveness probe used by the container healthcheck.',
               '', PUBLIC),
    'set_lang': (18, 1, 'Language Switch',
                 'Stores the interface language (en/ar/fr) in a cookie and returns to the referrer.',
                 '', PUBLIC),
    'set_lang_pair': (18, 3, 'Language Pair Switch',
                      'Switches the bilingual pair between Arabic/English and Arabic/French.',
                      '', PUBLIC),
    'favicon': (18, 2, 'Favicon',
                'Serves the application icon.',
                '', PUBLIC),
}

# Blueprint prefix -> handler file. Derived rather than hand-maintained, so a
# new blueprint only needs one entry here.
_TOP_LEVEL_FILES = {
    'index': 'app/__init__.py',
    'health': 'app/__init__.py',
    'set_lang': 'app/__init__.py',
    'set_lang_pair': 'app/__init__.py',
    'favicon': 'app/__init__.py',
    'admin': 'app/blueprints/admin/routes.py',
    'eshop': 'app/blueprints/eshop/routes.py',
}


def _handler_file(endpoint):
    """Best-effort source path of the view function behind ``endpoint``."""
    if endpoint in _TOP_LEVEL_FILES:
        return _TOP_LEVEL_FILES[endpoint]
    blueprint = endpoint.split('.', 1)[0]
    if blueprint in _TOP_LEVEL_FILES:
        return _TOP_LEVEL_FILES[blueprint]
    if blueprint.startswith('web_'):
        return 'app/blueprints/web/%s/routes.py' % blueprint[len('web_'):]
    if blueprint.startswith('mobile_'):
        return 'app/blueprints/mobile/%s/routes.py' % blueprint[len('mobile_'):]
    return ''


def build_index(app):
    """Resolve the registry against the live url map, once per process."""
    routes = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint == 'static':
            continue
        entry = routes.setdefault(rule.endpoint, {'rule': str(rule), 'methods': set()})
        entry['methods'].update(m for m in rule.methods if m in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH'))

    index = {}
    for endpoint, (module_no, seq, name, description, template, access) in PAGES.items():
        route = routes.get(endpoint, {})
        index[endpoint] = {
            'id': '%d.%d' % (module_no, seq),
            'name': name,
            'module': MODULES.get(module_no, 'Other'),
            'module_no': module_no,
            'description': description,
            'template': ('app/templates/' + template) if template else '',
            'handler': _handler_file(endpoint),
            'route': route.get('rule', ''),
            'methods': ', '.join(sorted(route.get('methods', []))),
            'access': access,
            'endpoint': endpoint,
        }
    return index


def register(app):
    """Attach the registry to ``app`` and expose ``page_info`` to templates."""
    index = build_index(app)
    app.extensions['page_registry'] = index

    # Endpoints present in the url map but missing from PAGES still deserve a
    # badge, so synthesise a card in the 99.x bucket instead of showing none.
    for endpoint, route in _unregistered(app, index):
        index[endpoint] = {
            'id': '99.%d' % route['n'],
            'name': endpoint.split('.')[-1].replace('_', ' ').title(),
            'module': 'Unregistered',
            'module_no': 99,
            'description': 'This endpoint has no registry entry yet.',
            'template': '',
            'handler': _handler_file(endpoint),
            'route': route['rule'],
            'methods': ', '.join(sorted(route['methods'])),
            'access': 'Unknown',
            'endpoint': endpoint,
        }

    @app.context_processor
    def _inject_page_info():
        return {'page_info': index.get(request.endpoint)}

    return index


def _unregistered(app, index):
    """(endpoint, route) pairs that exist in the app but have no PAGES entry."""
    seen = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint == 'static' or rule.endpoint in index:
            continue
        entry = seen.setdefault(rule.endpoint, {'n': len(seen), 'rule': str(rule), 'methods': set()})
        entry['methods'].update(m for m in rule.methods if m in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH'))
    return list(seen.items())
