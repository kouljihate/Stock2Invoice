# Changelog

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
