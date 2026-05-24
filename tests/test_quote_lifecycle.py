import re
import sys
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"
SEND_DELAY_S = 5
PAID_DELAY_S = 30


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


def _get_first_product(page):
    page.goto(f"{BASE_URL}/web/stock")
    page.wait_for_selector("table")
    rows = page.locator("table tbody tr")
    if rows.count() == 0:
        return None, None
    cells = rows.first.locator("td")
    sku = cells.nth(0).locator("code").inner_text() if cells.nth(0).locator("code").count() > 0 else cells.nth(0).inner_text()
    name = cells.nth(1).locator("a").inner_text() if cells.nth(1).locator("a").count() > 0 else ""
    return sku.strip(), name.strip()


def _get_first_customer(page):
    page.goto(f"{BASE_URL}/web/customers")
    page.wait_for_selector("table")
    rows = page.locator("table tbody tr")
    if rows.count() == 0:
        return None
    name_el = rows.first.locator("td").nth(1).locator("strong")
    if name_el.count() > 0:
        return name_el.inner_text().strip()
    return None


def _create_quote(page, customer_name, sku, product_name, price, n_items=1):
    page.goto(f"{BASE_URL}/web/quotes/create")
    page.wait_for_selector("select[name='customer_name']")
    page.select_option("select[name='customer_name']", label=customer_name)
    page.wait_for_timeout(300)

    # Fill first item row
    page.fill("input[name='sku']", sku)
    page.fill("input[name='quantity']", str(random.randint(1, 5)))
    page.fill("input[name='unit_price']", str(price))
    page.fill("input[name='name']", product_name or sku)


    # Add additional item rows
    for _ in range(1, n_items):
        page.click("#add-item")
        page.wait_for_timeout(150)
        rows = page.locator(".line-item")
        last = rows.nth(rows.count() - 1)
        last.fill("input[name='sku']", sku)
        last.fill("input[name='quantity']", str(random.randint(1, 5)))
        last.fill("input[name='unit_price']", str(random.randint(30, 300)))
        last.fill("input[name='name']", product_name or sku)


    page.click("button[type='submit']")
    try:
        page.wait_for_url(re.compile(r"/web/quotes/?$"), timeout=10000)
    except Exception:
        pass


def _send_quote(page, quote_id):
    page.goto(f"{BASE_URL}/web/quotes/{quote_id}")
    page.wait_for_selector("form[action*='/send'] button")
    page.click("form[action*='/send'] button")
    try:
        page.wait_for_url(re.compile(r"/web/quotes/"), timeout=8000)
    except Exception:
        pass


def _mark_invoice_paid(page, invoice_id):
    page.goto(f"{BASE_URL}/web/invoices/{invoice_id}")
    page.wait_for_selector("select[name='status']")
    page.select_option("select[name='status']", "paid")
    page.click("button[type='submit']")
    try:
        page.wait_for_url(re.compile(r"/web/invoices/"), timeout=8000)
    except Exception:
        pass


def _create_delivery_note(page, order_id, sku, product_name, n_items=1):
    page.goto(f"{BASE_URL}/web/delivery-notes/create")
    page.wait_for_selector("select[name='order_id']")
    page.select_option("select[name='order_id']", value=order_id)
    page.wait_for_timeout(500)

    # Fill first item row
    page.fill("input[name='sku']", sku)
    page.fill("input[name='quantity']", str(random.randint(1, 3)))
    if page.locator("input[name='name']").count() > 0:
        page.fill("input[name='name']", product_name)

    # Add additional item rows
    for _ in range(1, n_items):
        add_btn = page.locator("#add-item")
        if add_btn.count() == 0:
            break
        add_btn.click()
        page.wait_for_timeout(150)
        rows = page.locator(".line-item")
        last = rows.nth(rows.count() - 1)
        last.fill("input[name='sku']", sku)
        last.fill("input[name='quantity']", str(random.randint(1, 3)))

    page.click("button[type='submit']")
    try:
        page.wait_for_url(re.compile(r"/web/delivery-notes/?$"), timeout=10000)
    except Exception:
        pass


def _process_company(company, n_quotes, min_items=1, max_items=1):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            _login(page, company["email"], "admin@123")
            page.wait_for_url(re.compile(r"/(web/dashboard|admin)/?"), timeout=15000)

            sku, pname = _get_first_product(page)
            if not sku:
                print(f"  [{company['name']}] SKIP — no products")
                return
            cust_name = _get_first_customer(page)
            if not cust_name:
                print(f"  [{company['name']}] SKIP — no customers")
                return

            print(f"  [{company['name']}] SKU={sku}, Customer={cust_name}")

            for qi in range(1, n_quotes + 1):
                price = random.randint(50, 500)
                n_items = random.randint(min_items, max_items)
                try:
                    print(f"    [{company['name']}] Quote {qi}/{n_quotes}: create ({n_items} items)...")
                    _create_quote(page, cust_name, sku, pname or sku, price, n_items)

                    quote_id = _extract_latest_quote_id(page)
                    if not quote_id:
                        print(f"    [{company['name']}] Quote {qi}: FAIL — could not find quote ID")
                        continue
                    print(f"    [{company['name']}] Quote {qi}: id={quote_id}")

                    print(f"    [{company['name']}] Quote {qi}: sending...")
                    _send_quote(page, quote_id)

                    print(f"    [{company['name']}] Quote {qi}: waiting {SEND_DELAY_S}s before validate...")
                    time.sleep(SEND_DELAY_S)

                    print(f"    [{company['name']}] Quote {qi}: validating...")
                    page.goto(f"{BASE_URL}/web/quotes/{quote_id}")
                    page.wait_for_selector("form[action*='/validate'] button", timeout=10000)
                    with page.expect_navigation(timeout=15000):
                        page.click("form[action*='/validate'] button")
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(2000)

                    order_url = page.url
                    order_id = _extract_order_id(order_url)
                    print(f"    [{company['name']}] Quote {qi}: Order id={order_id}")

                    invoice_id = _get_latest_invoice_id(page)
                    if not invoice_id:
                        print(f"    [{company['name']}] Quote {qi}: FAIL — could not find invoice ID on order page")
                        continue
                    print(f"    [{company['name']}] Quote {qi}: Invoice id={invoice_id}")

                    print(f"    [{company['name']}] Quote {qi}: waiting {PAID_DELAY_S}s before marking paid...")
                    time.sleep(PAID_DELAY_S)

                    print(f"    [{company['name']}] Quote {qi}: marking invoice paid...")
                    _mark_invoice_paid(page, invoice_id)

                    print(f"    [{company['name']}] Quote {qi}: creating delivery note ({n_items} items)...")
                    _create_delivery_note(page, order_id, sku, pname or sku, n_items)

                    print(f"    ✓ [{company['name']}] Quote {qi} done")

                except Exception as e:
                    print(f"    ✗ [{company['name']}] Quote {qi} FAILED: {e}")

            print(f"  ✓ [{company['name']}] completed {n_quotes} quote(s)")
        except Exception as e:
            print(f"  ✗ [{company['name']}] FAILED: {e}")
        finally:
            browser.close()


def _extract_latest_quote_id(page):
    m = re.search(r"/web/quotes/([a-f0-9]{24})", page.url)
    if m:
        return m.group(1)
    rows = page.locator("table tbody tr")
    for i in range(rows.count()):
        link = rows.nth(i).locator("a[href*='/web/quotes/']").first
        if link.count() > 0:
            href = link.get_attribute("href") or ""
            m2 = re.search(r"/web/quotes/([a-f0-9]{24})", href)
            if m2:
                return m2.group(1)
    return None


def _extract_order_id(url):
    m = re.search(r"/web/orders/([a-f0-9]{24})", url)
    return m.group(1) if m else None


def _get_latest_invoice_id(page):
    page.goto(f"{BASE_URL}/web/invoices")
    try:
        page.wait_for_selector("table tbody tr", timeout=10000)
    except Exception:
        print(f"      [DEBUG] No invoice list table found at {page.url}")
        return None
    rows = page.locator("table tbody tr")
    if rows.count() == 0:
        print("      [DEBUG] No invoice rows found")
        return None
    for i in range(rows.count()):
        link = rows.nth(i).locator("a[href*='/web/invoices/']")
        if link.count() > 0:
            href = link.first.get_attribute("href") or ""
            m = re.search(r"/web/invoices/([a-f0-9]{24})", href)
            if m:
                return m.group(1)
    print("      [DEBUG] No invoice link with hex ID found in list")
    return None


def main():
    n_quotes = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    n_companies = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    n_workers = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    min_items = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    max_items = int(sys.argv[5]) if len(sys.argv) > 5 else 1

    print(f"Quotes per company: {n_quotes}, Companies: {n_companies}, Workers: {n_workers}, Items per quote: {min_items}-{max_items}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        _login(page, "admin@SI.ma", "admin@123")
        page.wait_for_url(re.compile(r"/admin/?"))
        all_companies = _get_companies(page)
        print(f"\nFound {len(all_companies)} companies total")

        enriched = []
        for c in all_companies[:n_companies]:
            email = _admin_email(page, c["id"])
            if email:
                enriched.append({"id": c["id"], "name": c["name"], "email": email})
                print(f"  {c['name']:35s} → {email}")
            else:
                print(f"  {c['name']:35s} → SKIP (no admin email)")

        browser.close()

    print(f"\nProcessing {len(enriched)} companies in parallel ({n_workers} workers)...")
    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        futures = {
            pool.submit(_process_company, c, n_quotes, min_items, max_items): c["name"]
            for c in enriched
        }
        for f in as_completed(futures):
            pass

    print("\nAll done.")


if __name__ == "__main__":
    main()
