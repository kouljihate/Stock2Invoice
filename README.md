# ProcureFlow

Flask web application for the full **Procure-to-Pay** and **Quote-to-Cash** lifecycle with MongoDB Atlas.

## Procure-to-Pay (Inbound)

```
Supplier → Purchase Order → Goods Receipt → Supplier Invoice → Payment
```

| Module | Description | Status |
|--------|-------------|--------|
| **Suppliers** | Manage vendor information, contacts, legal IDs | ✅ Ready |
| **Purchase Orders** | Create and send POs to suppliers | ⚙️ Skeleton |
| **Goods Receipt** | Receive inventory against POs | ⚙️ Skeleton |
| **Supplier Invoices** | Track bills from suppliers | ⚙️ Skeleton |
| **Payments** | Record payments and close transactions | ⚙️ Skeleton |

## Quote-to-Cash (Outbound)

```
Quote → Customer Order → Delivery Note → Customer Invoice
```

| Module | Description | Status |
|--------|-------------|--------|
| **Quotes** | Send quotes to customers | ⚙️ Skeleton |
| **Customer Orders** | Manage sales orders from customers | ✅ Implemented |
| **Delivery Notes** | Record goods dispatched to customers | ⚙️ Skeleton |
| **Customer Invoices** | Bill customers with status workflow | ✅ Implemented |

## Cross-Cutting

- **Products (Inventory)** — Stock tracking, movements, low-stock alerts
- **Multi-tenant** — Company-isolated data with role-based access (super_admin, company_admin, user)
- **Admin Panel** — Company and user management

## Quick Start

## Quick Start

```bash
# 1. Clone and enter the project
cd StockInvoice

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — set MONGO_URI (MongoDB Atlas) and SECRET_KEY

# 5. Create super admin (one-time)
flask create-super-admin admin@example.com yourpassword "Super Admin"

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
    config.py                 # Configuration from environment
    extensions/
      db.py                   # MongoDB, Bcrypt, JWT init
      logging.py              # Rotating file logger
    core/
      models/                 # Data access layer (PyMongo)
      services/               # Business logic layer
      validators/             # Input validation helpers
      utils/                  # Error handlers, pagination helpers
    blueprints/
      web/                    # Desktop routes (auth, dashboard, stock, invoices)
      mobile/                 # Mobile routes (same services, different templates)
    templates/                # Jinja2 with base layout + partials
    static/                   # CSS, JS, fonts
    logs/                     # Rotating log files
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
| `/web/orders/` | Order CRUD + status workflow (JWT required) |
| `/web/stock/` | Product CRUD (JWT required) |
| `/web/invoices/` | Invoice CRUD + print view (JWT required) |
| `/mobile/...` | Mobile equivalents of all web routes |
| `/lang/<code>` | Language switch (en/ar/fr) |
| `/api/health` | Health check |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | dev-secret-key | Flask session key |
| `MONGO_URI` | `mongodb://localhost:27017/stockinvoice` | MongoDB connection string |
| `JWT_SECRET_KEY` | jwt-dev-secret | JWT signing key |
| `JWT_ACCESS_TOKEN_EXPIRES` | 86400 | Token lifetime (seconds) |
| `FLASK_ENV` | development | runtime mode |
