# StockInvoice

Production-ready Flask web application for stock management and invoice generation with MongoDB Atlas.

## Features

- **Authentication** — Secure registration/login with bcrypt password hashing, JWT sessions
- **Dashboard** — Key metrics, low-stock alerts, recent activity, category breakdown
- **Stock Management** — CRUD products, SKU tracking, stock movements, low-stock thresholds, category valuation
- **Invoicing** — Create invoices with line items, discount/tax calculation, status workflow (draft → sent → paid → cancelled), printable HTML views
- **Web + Mobile** — Separate blueprints for `/web/` and `/mobile/` with responsive Bootstrap themes
- **Role-aware** — Admin vs regular user claim enforcement
- **Logging** — Rotating file logs for app activity and errors
- **3‑font i18n ready** — Comfortaa (EN),  Ruwudu (AR), Tangerine (FR) wired in CSS

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

# 5. Run
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

## API Endpoints

| Prefix | Description |
|--------|-------------|
| `/web/auth/` | Login, register, logout |
| `/web/dashboard/` | Dashboard (JWT required) |
| `/web/stock/` | Product CRUD (JWT required) |
| `/web/invoices/` | Invoice CRUD + print view (JWT required) |
| `/mobile/auth/` | Mobile login/register |
| `/mobile/...` | Mobile equivalents of all web routes |
| `/api/health` | Health check |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | dev-secret-key | Flask session key |
| `MONGO_URI` | `mongodb://localhost:27017/stockinvoice` | MongoDB connection string |
| `JWT_SECRET_KEY` | jwt-dev-secret | JWT signing key |
| `JWT_ACCESS_TOKEN_EXPIRES` | 86400 | Token lifetime (seconds) |
| `FLASK_ENV` | development | runtime mode |
