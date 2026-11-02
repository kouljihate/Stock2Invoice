# StockInvoice

Flask web application for the full **Procure-to-Pay**, **Quote-to-Cash**, **Services**, and **EShop** lifecycle with MongoDB and Role-Based Access Control.

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

## Services

| Module | Description | Status |
|--------|-------------|--------|
| **Services** | Service tracking, scheduling, and closure | Ready |

## EShop

| Module | Description | Status |
|--------|-------------|--------|
| **Public Catalog** | Browse products, add to cart | Ready |
| **Admin Panel** | Manage orders from the eshop | Ready |

## Cross-Cutting

- **Products (Inventory)** — Stock tracking, movements, low-stock alerts
- **Multi-tenant** — Company-isolated data with role-based access
- **Role-Based Access Control** — Permission → Role → User hierarchy with wildcard expansion
- **Admin Panel** — Company and user management, invoice template customization
- **Invoice PDF** — Server-side PDF via fpdf2 with per-company branding (colors, font, logo, header/footer)
- **Arrêté** — Auto-generated French legal closing on PDF: amount in words
- **Multi-language** — EN/AR/FR with language switcher
- **RabbitMQ Monitor** — Admin-only live broker metrics (queues, connections, channels, consumers, backlog, alarms, busiest queues) on the admin dashboard, read from the management HTTP API

## Profiles & Onboarding

The application is built around two user profiles:

| Profile | Scope | Created by |
|---|---|---|
| **Admin** | Platform: manages **all** other user profiles, companies and settings. **Exactly one** Admin account is allowed — the CLI (`flask create-super-admin`, `flask promote <email> Admin`) and the admin panel both refuse to mint a second one. | `flask create-super-admin` (first run) |
| **PME-Admin** | One PME (small business): his **own stock, own customers and own users**, fully isolated from every other company. | Admin panel → *Create PME-Admin* |

Inside a company, an owner can additionally grant the **Manager** and **Customer** roles.

**First login:** a PME-Admin is created *without* a company. On his first login he is redirected to `/web/profile/setup`, a wizard that collects his personal information (name, phone) and his company's (name, address, city, contacts, ICE/RC/IF/CNSS). Only after submitting it does his company — and therefore his private data space — come into existence; until then every application area redirects to the wizard. The platform Admin never sees it.

## Quick Start

```bash
# 1. Clone and enter the project
cd StockInvoice

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate      # Windows

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt   # only needed to run the test suite

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
        user_model.py         # User with roles array, permission expansion
        role_model.py         # Role with permission strings
        permission_model.py   # Permission catalog
      services/               # Business logic layer
        pdf_service.py        # fpdf2-based invoice PDF generation
      validators/             # Input validation helpers
      utils/
        permissions.py        # Wildcard expansion, ALL_PERMISSIONS list
        number_to_french.py   # Convert numbers to French words
    blueprints/
      web/                    # Desktop routes (auth, dashboard, stock, invoices...)
      mobile/                 # Mobile routes (same services, different templates)
      admin/                  # Super admin panel (companies, users)
      eshop/                  # EShop public + admin routes
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
| `flask bootstrap` | Seed the RBAC roles and create the MongoDB indexes (idempotent; also runs at startup) |
| `flask promote <email> <role>` | Set a user's role — `Admin`, `Manager` or `Customer` |

> Use `python -m flask ...` if the `flask` executable on your `PATH` belongs to
> a different Python than the one with the dependencies installed.

## Tests

```bash
python -m pytest                                   # unit tests (no server, no data written)
RUN_E2E=1 python -m pytest tests/test_create_company.py   # Playwright walkthroughs
```

The script-style helpers in `tests/` (data generators, connection checks) are
not collected by pytest — run them directly with `python tests/<file>`.

## Production

```bash
gunicorn -c gunicorn.conf.py app:app
```

Set `COOKIE_SECURE=1` behind HTTPS, keep `FLASK_DEBUG` unset/0, and never ship
the example `SECRET_KEY` / `JWT_SECRET_KEY` values — production refuses to
start while either is a placeholder.

## Routes

| Prefix | Description |
|--------|-------------|
| `/admin/` | Super admin panel (companies, users) |
| `/web/auth/` | Login, register, logout |
| `/web/dashboard/` | Dashboard (JWT required) |
| `/web/customers/` | Customer CRUD |
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
| `/web/users/` | Company user management |
| `/web/events/` | Activity log |
| `/web/services/` | Service tracking |
| `/eshop/` | Public catalog + admin panel |
| `/mobile/...` | Mobile equivalents of all web routes |
| `/lang/<code>` | Language switch (en/ar/fr) |
| `/api/health` | Health check |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | dev-secret-key | Flask session key (**must** be a random value of 32+ chars) |
| `RABBITMQ_URL` | `amqp://guest:guest@rabbitmq:5672/%2f` | AMQP endpoint; the admin dashboard monitor derives the management API host/credentials from it. `RABBITMQ_MGMT_URL` overrides the full management URL. |
| `MONGO_URI` | `mongodb://localhost:27017/stockinvoice` | MongoDB connection string |
| `JWT_SECRET_KEY` | jwt-dev-secret | JWT signing key (**must** be a random value of 32+ chars) |
| `JWT_ACCESS_TOKEN_EXPIRES` | 3600 | Token lifetime (seconds) |
| `COOKIE_SECURE` | 0 | Set `1` when serving over HTTPS |
| `ALLOW_PUBLIC_REGISTRATION` | 0 | Enable self-service sign-up (accounts are created without a company) |
| `AUTH_RATE_LIMIT` | 10 | Auth attempts allowed per client per window |
| `AUTH_RATE_WINDOW` | 300 | Auth throttle window (seconds) |
| `FLASK_ENV` | development | runtime mode |
| `FLASK_DEBUG` | 0 | `1` enables the Werkzeug debugger — local use only |
| `PORT` | 5002 | App port (overridden by `PORT` env var) |

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
