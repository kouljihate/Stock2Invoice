# Changelog

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
