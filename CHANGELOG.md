# Changelog

## [2.5.1] — 2026-09-09
### Fixed
- Gunicorn WSGI load: expose `app=create_app()` on app package, reuse in `run.py`

## [2.5.0] — 2026-09-09
### Added
- Admin quick password reset from the login page: fill Email, click **Reset Password** to reset `admin@SI.ma` to `admin123` directly (no old/new password prompts)
- Global exception handling: uncaught route errors now return a clear message with script name, function name, line number, and error description (HTML + JSON)
- Ctrl+C (KeyboardInterrupt) handling in `run.py` that stops the server with a clear "Application terminated by user" message
- `error_context()` helper in `app/core/utils/helpers.py` for formatted error reporting

### Changed
- Default port: `5000` → `5002`
- MONGO_URI points to local MongoDB (`mongodb://localhost:27017/stockinvoice`) in `.env.example`
- Flash/alert messages now appear as stacked toasts in the top-right corner and auto-dismiss after 5 seconds
- Arabic font changed to **VIP Rawy Thin** (bundled in `app/static/fonts/`)
- General → Users: Administrator role users now list **all** users for management instead of a "No company assigned" error
- Error 500 page now displays the detailed error context message

### Fixed
- `ImportError: cannot import name 'bcrypt' from 'app.extensions'` — use `app.extensions.db.bcrypt`
- Admin user lookup on reset now correctly matches the stored lowercase `admin@si.ma` email

## [2.4.0] — 2026-05-29
### Added
- `static/css/tables.css` — centralized table styling (16px thead, 14px tbody default, 12px compact variant)
- Local Bootswatch BRITE theme (`static/css/themes/brite.css`) replaces CDN Bootstrap

### Changed
- All list tables: removed inline `font-size`, removed `small` class, now inherit from `tables.css`
- Tables default to `vertical-align: middle` on all cells (eliminates `align-middle` boilerplate)
- Delivery Notes table uses `table-sm-compact` class for 12px tbody

### Fixed
- Auth card width: `display:flex` on main caused inner `.row` to shrink — added `width:100%` to `.auth-body main .row`
- `NameError: name 'OrderModel' is not defined` in `order_service.py` — changed to `CustomerOrderModel`
- Quotes, Orders, Invoices, Customer Quotes, Delivery Notes tables: consistent font sizing
- Loader overlay on form submit, button click, nav-link click

## [2.3.0] — 2026-05-28
### Added
- `fixes/` and `migrations/` directories to organise one-time scripts

### Changed
- Role collection: `_id` changed from ObjectId to lowercase role name (e.g., `"manager"`) — all role lookups use `_id` directly
- Sidebar: Admin users now see only General module with Companies, All Users, Activity Log; all other modules (P2P, Q2C, EShop) hidden
- General module sub-items split: Admin users see only admin items (Companies, All Users, Activity Log), non-admin users see Products/Stock and Users
- UserModel role lookup query switched from `{'name': {'$in': role_names}}` to `{'_id': {'$in': [n.lower() for n in role_names]}}`

### Fixed
- EShop routes: `abort(403)` import and usage for unauthorized admin access

## [2.2.0] — 2026-05-28
### Added
- Role-Based Access Control (RBAC): Permission and Role collections, wildcard permission expansion
- EShop module: public product listing, admin panel with order management
- Services module: service view, creation, scheduling, and closure workflows
- `general.companies`, `general.allusers`, `general.activities` permissions for admin sidebar gating
- `eshop.administration`, `eshop.link` permissions
- Dedicated 403 Forbidden error page with card layout and descriptive message
- `abort(403)` enforcement on admin, eshop admin, and company-admin routes

### Changed
- Sidebar: all modules (Q2C, P2P, EShop, General) shown to all users; only admin items (Companies, All Users, Activity Log) remain permission-gated
- User model: replaced single `role` string with `roles` array (role-name strings from Role collection)
- Permission model: expanded from simple access flags to 26+ concrete permissions with wildcard support (`*`, `module.*`)
- Dashboard user aggregation: switched from `$group` on old `role` field to `$unwind` on `roles` array
- Error pages: now auto-detect web/mobile mode and attempt to load logged-in user for context
- All Companies table: rows vertically aligned to middle

### Fixed
- `NoneType` object is not subscriptable error on admin dashboard (aggregate grouping on removed `role` field)
- `NameError: name 'RoleModel' is not defined` in admin routes (missing import)
- Sidebar permission check for EShop sub-items now uses combined `user.permissions` from effective role expansion

## [2.1.0] — 2026-05-24
### Added
- Server-side PDF generation via fpdf2 (pure Python, no external deps)
- Comfortaa font embedded in PDF
- Per-company invoice template customization (colors, font, header/footer text, visibility toggles)
- `number_to_french.py` utility: converts totals to French words (dirhams/centimes)
- Dynamic Arrêté in PDF: "Arrêtée la présente facture à la somme de X MAD (en lettres : Y)"
- City field on invoice and quote forms (col-md-4 next to Address)
- `min_of_items`/`max_of_items` CLI args on test_quote_lifecycle.py
- Subtitle below logo in PDF header: "Equipement d'eau potable, Eau du bien-être, Spa et piscines."
- Arabic/French translations

### Changed
- PDF layout: 20/70/10 A4 partition (header/body/footer)
- INVOICE title + ref on same row, Attention To right-aligned on same row
- Notes always rendered as fixed French message at bottom of body
- Logo size increased (w=50 → w=70)
- Sidebar restructured with Bootstrap 5 collapse dropdowns (P2P/Q2C/General)
- Invoice print template uses dynamic company invoice_template settings

### Fixed
- Data isolation: company_id ownership checks across all 9 blueprint files
- Service layer: StockService, OrderService, InvoiceService check company_id
- Logo upload: `os.path.splitext` base vs extension bug
- InvoiceModel.to_dict() missing customer_city, customer_country, arrete fields

## [1.3.0] — 2026-05-22
### Added
- Customers module: CRUD + bulk upload
- Delivery Notes module: create, list, delete
- Customer Quotes: customer dropdown from DB, Add Customer modal (AJAX), product lookup auto-fill
- Quote actions: Send, Validate (→ confirmed order + auto-invoice), Delete
- Delete buttons on Orders, Delivery Notes, and Invoices list & detail views
- Circular action buttons (`.btn-icon-circle`) throughout

### Changed
- Currency: `$` → `MAD` across all modules
- Supplier model: updated fields (ICE, RC, Payment Terms, City)
- Customer model: added type (prive/company), ICE, RC, paiement_terms

### Fixed
- `.items` dict method bug in Jinja2 templates (6 files)
- Order detail, printable, invoice detail/print templates

## [1.2.0] — 2026-05-21
### Added
- Suppliers module: CRUD + bulk upload
- Purchase Orders: create, list, view with line items
- Goods Receipt: create, list
- Supplier Invoices: create, list, view
- Payments: create, list
- Bulk upload two-step flow (CSV/JSON → preview → validate)
- Company info bar in layout header

### Changed
- Product model: 15-field format
- Translation system: EN/AR/FR with language switcher

## [1.1.0] — 2026-05-20
### Added
- Customer Quotes module
- Customer Orders PDF download
- Share button (Web Share API)
- Order → Invoice auto-generation

## [1.0.0] — 2026-05-19
### Added
- Initial release
- Authentication (JWT + bcrypt)
- Multi-tenant (super_admin → company_admin → user)
- Admin panel (companies, users)
- Products CRUD
- Invoices CRUD
- Dashboard with stats
- Mobile blueprint
- Language switching EN/AR/FR
- PDF generation via weasyprint
