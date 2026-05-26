# Project Summary

## Overview
StockInvoice is a Flask + MongoDB multi-tenant business application that supports both Procure-to-Pay and Quote-to-Cash workflows.

## Core Capabilities
- Procure-to-Pay: Suppliers, Purchase Orders, Goods Receipt, Supplier Invoices, Payments
- Quote-to-Cash: Customer Quotes, Orders, Delivery Notes, Customer Invoices
- Shared modules: Inventory/Stock, Events, Users, Admin panel, language switching (EN/AR/FR)

## Tech Stack
- Backend: Flask 3.1, PyMongo, Flask-JWT-Extended, Flask-Bcrypt
- Database: MongoDB
- Templates/UI: Jinja2 + static CSS/JS (web + mobile blueprints)
- Document output: fpdf2 (invoice PDF generation), weasyprint dependency present

## Architecture Snapshot
- App factory in `app/__init__.py`
- Route organization by blueprints: `/web/*`, `/mobile/*`, `/admin/*`
- Layered folders for models/services/validators/utils under `app/core/*`
- Automated data-generation/lifecycle scripts under `tests/`

## Current Version
- Version: 2.1.0
- Build date: 2026-05-24

## Notable Observations
- The codebase appears feature-rich and well-structured for CRUD-heavy workflows.
- There is duplication in folder conventions (`app/models` vs `app/core/models`, `app/services` vs `app/core/services`) that may increase maintenance overhead.
- `CHANGELOG.md` contains text encoding artifacts that should be normalized to UTF-8.

## Suggested Next Steps
1. Consolidate duplicated model/service structure into one canonical layer.
2. Normalize text encoding in docs/changelog and enforce UTF-8 in editor/tooling.
3. Run and document a baseline test pass to confirm current stability.
