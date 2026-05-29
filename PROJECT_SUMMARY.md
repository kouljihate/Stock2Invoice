# Project Summary

## Overview
StockInvoice is a Flask + MongoDB multi-tenant business application that supports Procure-to-Pay, Quote-to-Cash, Services, and EShop workflows with full Role-Based Access Control.

## Core Capabilities
- Procure-to-Pay: Suppliers, Purchase Orders, Goods Receipt, Supplier Invoices, Payments
- Quote-to-Cash: Customer Quotes, Orders, Delivery Notes, Customer Invoices
- Services: Service tracking with scheduling and closure workflows
- EShop: Public product catalog with admin order management panel
- Shared: Inventory/Stock, Users, Events/Activity Log, Admin panel, language switching (EN/AR/FR)
- RBAC: Permission → Role → User hierarchy with wildcard expansion and route-level 403 enforcement

## Tech Stack
- Backend: Flask 3.1, PyMongo, Flask-JWT-Extended, Flask-Bcrypt
- Database: MongoDB (local or Atlas)
- Templates/UI: Jinja2 + Bootstrap 5 + static CSS/JS (web + mobile blueprints)
- Document output: fpdf2 (invoice PDF generation)

## Architecture Snapshot
- App factory in `app/__init__.py`
- Route organization by blueprints: `/web/*`, `/mobile/*`, `/admin/*`, `/eshop/*`
- Layered folders for models/services/validators/utils under `app/core/*`
- Automated data-generation/lifecycle scripts under `tests/`

## Current Version
- Version: 2.3.0
- Build date: 2026-05-28

## Notable Observations
- The codebase is feature-rich and well-structured for CRUD-heavy workflows with multi-tenant isolation.
- Permission system uses string identifiers with wildcard expansion (`*`, `module.*`) for flexible role definition.
- Users store roles as role-name strings (e.g., `['Admin']`, `['Manager']`); effective permissions computed at runtime.

## Suggested Next Steps
1. Add route-level permission decorators using `has_perm()` for fine-grained access control.
2. Add setting-based per-company role/visibility configuration.
3. Expand test coverage for RBAC edge cases (wildcard expansion, multi-role users).
