# StockInvoice

Flask web application for the full **Procure-to-Pay** and **Quote-to-Cash** lifecycle with MongoDB.

## Procure-to-Pay (Inbound)

```
Supplier → Purchase Order → Goods Receipt → Supplier Invoice → Payment
```

| Module | Description | Status |
|--------|-------------|--------|
| **Suppliers** | Manage vendor information, contacts, legal IDs | Ready |
| **Purchase Orders** | Create and send POs to suppliers | Ready |
| **Goods Receipt** | Receive inventory against POs | Ready |
| **Supplier Invoices** | Track bills from suppliers | Ready |
| **Payments** | Record payments and close transactions | Ready |

## Quote-to-Cash (Outbound)

```
Quote → Customer Order → Delivery Note → Customer Invoice
```

| Module | Description | Status |
|--------|-------------|--------|
| **Quotes** | Send quotes to customers, multi-item, validate → Order + Invoice | Ready |
| **Customer Orders** | Manage sales orders from customers | Ready |
| **Delivery Notes** | Record goods dispatched to customers | Ready |
| **Customer Invoices** | Bill customers with status workflow, PDF download | Ready |

## Cross-Cutting

- **Products (Inventory)** — Stock tracking, movements, low-stock alerts
- **Multi-tenant** — Company-isolated data with role-based access (super_admin, company_admin, user)
- **Admin Panel** — Company and user management, invoice template customization
- **Invoice PDF** — Server-side PDF via fpdf2 with per-company branding (colors, font, logo, header/footer)
- **Arrêté** — Auto-generated French legal closing on PDF: amount in words
- **Multi-language** — EN/AR/FR with language switcher

## Quick Start

```bash
# 1. Clone and enter the project
cd StockInvoice

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate      # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — set MONGO_URI and SECRET_KEY

# 5. Create super admin (one-time)
flask create-super-admin admin@SI.ma admin@123 "Super Admin"

# 6. Run
python run.py
```

## Project Structure

```
StockInvoice/
  run.py
  requirements.txt
  .env.example
  app/
    __init__.py               # App factory, blueprint registration
    version.py                # VERSION + BUILD_DATE
    config.py                 # Configuration from environment
    extensions/
      db.py                   # MongoDB, Bcrypt, JWT init
      logging.py              # Rotating file logger
    core/
      models/                 # Data access layer (PyMongo)
      services/               # Business logic layer
        pdf_service.py        # fpdf2-based invoice PDF generation
      validators/             # Input validation helpers
      utils/
        number_to_french.py   # Convert numbers to French words
    blueprints/
      web/                    # Desktop routes (auth, dashboard, stock, invoices...)
      mobile/                 # Mobile routes (same services, different templates)
    templates/                # Jinja2 with base layout + partials
    static/                   # CSS, JS, fonts (Comfortaa)
    logs/                     # Rotating log files
  tests/
    test_create_company.py
    test_create_related.py
    test_quote_lifecycle.py
    test_p2p_procurement.py
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `flask create-super-admin <email> <password> [name]` | Create initial super admin |

## Routes

| Prefix | Description |
|--------|-------------|
| `/admin/` | Super admin panel (companies, users) |
| `/web/auth/` | Login, register, logout |
| `/web/dashboard/` | Dashboard (JWT required) |
| `/web/quotes/` | Quote CRUD + send/validate workflow |
| `/web/orders/` | Order CRUD + status workflow |
| `/web/stock/` | Product CRUD |
| `/web/invoices/` | Invoice CRUD + PDF download |
| `/web/delivery-notes/` | Delivery note CRUD |
| `/web/suppliers/` | Supplier CRUD |
| `/web/purchase-orders/` | PO CRUD |
| `/web/goods-receipt/` | Goods receipt CRUD |
| `/web/supplier-invoices/` | Supplier invoice CRUD |
| `/web/payments/` | Payment CRUD |
| `/mobile/...` | Mobile equivalents of all web routes |
| `/lang/<code>` | Language switch (en/ar/fr) |
| `/api/health` | Health check |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | dev-secret-key | Flask session key |
| `MONGO_URI` | `mongodb://localhost:27017/maure_stc` | MongoDB connection string |
| `JWT_SECRET_KEY` | jwt-dev-secret | JWT signing key |
| `JWT_ACCESS_TOKEN_EXPIRES` | 86400 | Token lifetime (seconds) |
| `FLASK_ENV` | development | runtime mode |

## Test Scripts

```bash
# Create 50 companies with Moroccan names and logos
python tests/test_create_company.py 50

# Create related entities (customers, suppliers, products) in parallel
python tests/test_create_related.py 50 5

# Q2C lifecycle: quote → order → invoice → paid → delivery note
python tests/test_quote_lifecycle.py <n_quotes> <n_companies> <n_workers> <min_items> <max_items>

# P2P lifecycle: PO → goods receipt → supplier invoice → payment
python tests/test_p2p_procurement.py <n_cycles> <n_companies> <n_workers>
```
