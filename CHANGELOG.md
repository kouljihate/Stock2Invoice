# Changelog

## [2.9.0] - 2026-11-03
### Added
- Per-user typography controls in Edit Profile: independently choose Small,
  Default, or Large text for English/French and Arabic. The selection is
  saved to the account and applied across every page.

## [2.8.0] — 2026-11-02
### Added
- **Dual-language interface**: every screen renders Arabic alongside English or
  French, chosen from the username menu (**العربية / English** = `ar-en`,
  default; **العربية / Français** = `ar-fr`), stored in the `lang_pair` cookie
  through `/lang/pair/<pair>`
  - `app/core/utils/i18n.py` — `dual()` helper emitting
    `<span class="dual"><span class="d-p" lang="en|fr">…</span><span class="d-s" lang="ar" dir="rtl">…</span></span>`;
    `_()` still returns plain text so `placeholder`, `title`, `alt`,
    `aria-label` and `<option>` stay valid, and it now follows the pair's
    primary language
  - `app/static/css/dual-lang.css` — arrangement decided per context: navbar
    as 3 columns (English left / user menu centre / Arabic right), card
    headers as English · logo · Arabic, buttons and table headers with Arabic
    on top, labels as two columns with English right and Arabic left
  - 1166 text elements converted to `dual()` across 61 templates; untranslated
    keys render once instead of duplicating the primary language
  - unknown pair values fall back to `ar-en`
- Page identity registry (`app/core/utils/page_registry.py`): 112 entries
  across 19 modules with `<module>.<sequence>` IDs (login = `0.0`), built at
  start-up from `app.url_map` so no screen is missing or stale
- Floating page badge on every screen, opening a dialog with the page ID, name,
  module, description, route, endpoint, template file, handler file and
  required access level
- Company logo upload in the setup wizard (`app/core/utils/uploads.py`,
  4 MB limit, png/jpg/jpeg/gif/webp); the logo fills the middle column of every
  card header
- `/web/profile/edit` — Edit Profile page, reachable from the username menu
- Seed fixtures in `tests/seed_data/`: 10 PME-Admin tenants with 100 customers
  and 50 suppliers each (CSV), plus a deterministic generator

### Changed
- Arabic typography: **VIP Rawy** is now a real font family (Regular 400, Bold
  700, Thin 300) and the default Arabic face via `--font-arabic`; `Comfortaa`
  keeps the Latin UI, with VIP Rawy listed as its fallback so untagged Arabic
  still renders correctly
- Navbar rebuilt as a 3-column grid; the globe language dropdown is replaced by
  the two pairs inside the username menu
- `body.has-navbar main` gains `1.25rem` top spacing

### Fixed
- `'VIP Rawy'` was requested by `.brand-ar` but never declared with
  `@font-face`, so the Arabic brand column silently fell back to Rajdhani
- Arabic font rules were keyed to `html[data-lang="ar"]`, which the
  dual-language switch never sets (`data-lang` is now only `en` or `fr`), so
  Arabic text received no Arabic font at all

## [2.7.0] — 2026-11-02
### Added
- Admin-only **RabbitMQ Monitor** on the Admin dashboard: broker version, cluster, queues, connections, channels, consumers, message totals (ready/unacked), alarms and the five busiest queues, read from the management HTTP API (`/api/overview`, `/api/queues`)
- `app/core/services/rabbitmq_service.py` — read-only management-API client that derives its endpoint and credentials from `RABBITMQ_URL` (or `RABBITMQ_MGMT_URL`), with a 2s timeout and a graceful **Offline** state instead of raising
- Login page rebuilt: fixed header bar, **Login** / **Reset Password** tabs on a single page, and a fixed three-column footer (copyright / tagline / version badge)
- `RABBITMQ_URL` added to the `bff` service environment so the dashboard can reach the broker

### Changed
- Auth page layout is now an exact **5% header / 90% content / 5% footer** viewport split
- `web_auth.forgot_password` POST answers re-render the tabbed login page with the Reset tab active instead of a separate page
- Login footer version is displayed inside a neon badge

### Fixed
- Login rejected valid addresses whose domain has no DNS record: `email_validator` deliverability checking is now disabled (`check_deliverability=False`), so DNS resolution can never block sign-in
- Login page footer stretched to the full content height because a blanket `.auth-body .row` rule also matched the footer's own row

## [2.6.0] — 2026-09-09
### Added
- Full session activity logging from login to logout:
  - Every action logged to `app/logs/app.log` with user identity, IP, method, path, status code, and duration
  - `before_request`/`after_request` hooks attach the JWT user context to each request
  - `login`/`logout` session markers recorded in the Activity Log (`events` collection) and as `SESSION START`/`SESSION END` log lines
  - `user_name`/`user_email` JWT claims included for readable user attribution
- Static assets, favicon, health checks, and CORS preflights excluded from access logging

### Changed
- Log format now uses the acting user (`Name (id)`) instead of a generic `anonymous`
- Web and mobile login claims enriched with `user_name`/`user_email`

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
