import re
import sys
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"
CITIES = ["Casablanca", "Rabat", "Marrakech", "Fes", "Tanger", "Agadir", "Oujda", "Meknes"]
CATEGORIES = ["Electronics", "Food", "Chemicals", "Textile", "Furniture", "Packaging"]
BRANDS = ["Premium", "Standard", "Eco", "Pro", "Elite"]


def _get_companies(page):
    page.goto(f"{BASE_URL}/admin/companies")
    page.wait_for_selector("table#companiesTable")
    companies = []
    rows = page.locator("table#companiesTable tbody tr")
    for i in range(rows.count()):
        strong = rows.nth(i).locator("strong")
        if strong.count() == 0:
            continue
        name = strong.inner_text()
        href = rows.nth(i).locator("a[href*='/admin/companies/']").first.get_attribute("href") or ""
        m = re.search(r"/admin/companies/([a-f0-9]+)", href)
        if m:
            companies.append({"id": m.group(1), "name": name})
    return companies


def _admin_email(page, cid):
    page.goto(f"{BASE_URL}/admin/companies/{cid}", wait_until="networkidle")
    if not page.locator("#tabUsers").count():
        print(f"    [WARN] #tabUsers missing at {page.url[:80]}")
        return None
    rows = page.locator("#tabUsers table tbody tr")
    for i in range(rows.count()):
        role_sel = rows.nth(i).locator("select[name='role']")
        if role_sel.count() > 0 and role_sel.input_value() == "company_admin":
            return rows.nth(i).locator("td").nth(1).inner_text()
    if rows.count() > 0:
        return rows.first.locator("td").nth(1).inner_text()
    return None


def _login(page, email, password):
    page.goto(f"{BASE_URL}/web/auth/login")
    page.wait_for_selector("input[name='email']")
    page.fill("input[name='email']", email)
    page.fill("input[name='password']", password)
    page.click("button[type='submit']")


def _create_products(page, count, label, suffix):
    for i in range(count):
        sku = f"SKU-{label[:4]}{suffix}{i}"
        name = f"Product {i+1} {label} {suffix[-4:]}{i}"
        page.goto(f"{BASE_URL}/web/stock/create")
        page.wait_for_selector("input[name='sku']")
        page.fill("input[name='sku']", sku)
        page.fill("input[name='name']", name)
        page.fill("input[name='brand']", random.choice(BRANDS))
        page.fill("input[name='category']", random.choice(CATEGORIES))
        page.fill("input[name='price']", str(random.randint(10, 999)))
        page.fill("input[name='quantity']", str(random.randint(10, 999)))
        page.fill("input[name='quantity_min']", str(random.randint(1, 20)))
        page.click("button[type='submit']")
        try:
            page.wait_for_url(re.compile(r"/web/stock/?$"), timeout=8000)
        except Exception:
            pass
        print(f"      Product {i+1}/{count}")


def _create_suppliers(page, count, label, suffix):
    for i in range(count):
        name = f"Supplier {i+1} {label} {suffix}{i}"
        page.goto(f"{BASE_URL}/web/suppliers/create")
        page.wait_for_selector("input[name='name']")
        page.fill("input[name='name']", name)
        page.fill("input[name='contact_name']", f"Contact {label}")
        page.fill("input[name='email']", f"s.{label.lower().replace(' ','')}{suffix}{i}@sup.ma")
        page.fill("input[name='phone']", f"+212 6{random.randint(10,99)}{random.randint(10,99)}{random.randint(10,99)}{random.randint(10,99)}")
        page.fill("input[name='city']", random.choice(CITIES))
        page.fill("input[name='payment_terms']", random.choice(["Net 30", "Net 60", "Cash"]))
        page.click("button[type='submit']")
        try:
            page.wait_for_url(re.compile(r"/web/suppliers/?$"), timeout=8000)
        except Exception:
            pass
        print(f"      Supplier {i+1}/{count}")


def _create_customers(page, count, label, suffix):
    for i in range(count):
        name = f"Customer {i+1} {label} {suffix}{i}"
        page.goto(f"{BASE_URL}/web/customers/create")
        page.wait_for_selector("select[name='type']")
        page.select_option("select[name='type']", random.choice(["prive", "company"]))
        page.fill("input[name='name']", name)
        page.fill("input[name='contact']", f"Contact {label}")
        page.fill("input[name='email']", f"c.{label.lower().replace(' ','')}{suffix}{i}@cust.ma")
        page.fill("input[name='phone']", f"+212 6{random.randint(10,99)}{random.randint(10,99)}{random.randint(10,99)}{random.randint(10,99)}")
        page.fill("input[name='city']", random.choice(CITIES))
        page.click("button[type='submit']")
        try:
            page.wait_for_url(re.compile(r"/web/customers/?$"), timeout=8000)
        except Exception:
            pass
        print(f"      Customer {i+1}/{count}")


def _process_company(company, n_products, n_suppliers, n_customers):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        suffix = datetime.now().strftime("%f")[:4]
        try:
            _login(page, company["email"], "admin@123")
            page.wait_for_url(re.compile(r"/(web/dashboard|admin)/?"), timeout=15000)

            label = company["name"].split()[0]

            print(f"  [{company['name']}] Products...")
            _create_products(page, n_products, label, suffix)
            print(f"  [{company['name']}] Suppliers...")
            _create_suppliers(page, n_suppliers, label, suffix)
            print(f"  [{company['name']}] Customers...")
            _create_customers(page, n_customers, label, suffix)
            print(f"  ✓ {company['name']} done")
        except Exception as e:
            print(f"  ✗ {company['name']} FAILED: {e}")
        finally:
            browser.close()


def main():
    n_products = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    n_suppliers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    n_customers = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    n_workers = int(sys.argv[4]) if len(sys.argv) > 4 else 5

    print(f"Products: {n_products}, Suppliers: {n_suppliers}, Customers: {n_customers}, Workers: {n_workers}")

    # ── Step 1: collect companies + admin emails (sequential) ──
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        _login(page, "admin@SI.ma", "admin@123")
        page.wait_for_url(re.compile(r"/admin/?"))
        companies = _get_companies(page)
        print(f"\nFound {len(companies)} companies")

        enriched = []
        for c in companies:
            email = _admin_email(page, c["id"])
            if email:
                enriched.append({"id": c["id"], "name": c["name"], "email": email})
                print(f"  {c['name']:35s} → {email}")
            else:
                print(f"  {c['name']:35s} → SKIP (no admin email)")

        browser.close()

    # ── Step 2: process all companies in parallel ──
    print(f"\nProcessing {len(enriched)} companies in parallel ({n_workers} workers)...")
    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        futures = {
            pool.submit(_process_company, c, n_products, n_suppliers, n_customers): c["name"]
            for c in enriched
        }
        for f in as_completed(futures):
            pass

    print("\nAll done.")


if __name__ == "__main__":
    main()
