import re
import sys
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"
CITIES = ["Casablanca", "Rabat", "Marrakech", "Fes", "Tanger", "Agadir", "Oujda", "Meknes"]


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


def _get_or_create_supplier(page, suffix):
    page.goto(f"{BASE_URL}/web/suppliers")
    try:
        page.wait_for_selector("table tbody tr", timeout=5000)
    except Exception:
        pass
    rows = page.locator("table tbody tr")
    if rows.count() > 0:
        name_el = rows.first.locator("td").nth(0).locator("strong")
        if name_el.count() > 0:
            name = name_el.inner_text().strip()
            edit_link = rows.first.locator("a[href*='/web/suppliers/']")
            if edit_link.count() > 0:
                href = edit_link.first.get_attribute("href") or ""
                m = re.search(r"/web/suppliers/([a-f0-9]{24})", href)
                if m:
                    return {"id": m.group(1), "name": name}

    name = f"Supplier P2P {suffix}"
    page.goto(f"{BASE_URL}/web/suppliers/create")
    page.wait_for_selector("input[name='name']")
    page.fill("input[name='name']", name)
    page.fill("input[name='contact_name']", f"Contact {suffix}")
    page.fill("input[name='email']", f"p2p.{suffix}@sup.ma")
    page.fill("input[name='phone']", f"+212 6{random.randint(10,99)}{random.randint(10,99)}{random.randint(10,99)}{random.randint(10,99)}")
    page.fill("input[name='city']", random.choice(CITIES))
    page.fill("input[name='payment_terms']", "Net 30")
    page.click("button[type='submit']")
    try:
        page.wait_for_url(re.compile(r"/web/suppliers/?$"), timeout=8000)
    except Exception:
        pass
    page.goto(f"{BASE_URL}/web/suppliers")
    try:
        page.wait_for_selector("table tbody tr", timeout=5000)
    except Exception:
        pass
    rows = page.locator("table tbody tr")
    if rows.count() > 0:
        name_el = rows.first.locator("td").nth(0).locator("strong")
        if name_el.count() > 0:
            name = name_el.inner_text().strip()
            edit_link = rows.first.locator("a[href*='/web/suppliers/']")
            if edit_link.count() > 0:
                href = edit_link.first.get_attribute("href") or ""
                m = re.search(r"/web/suppliers/([a-f0-9]{24})", href)
                if m:
                    return {"id": m.group(1), "name": name}
    return None


def _create_po(page, supplier_id, supplier_name, sku, pname, price):
    page.goto(f"{BASE_URL}/web/purchase-orders/create")
    page.wait_for_selector("select[name='supplier_id']")
    page.select_option("select[name='supplier_id']", value=supplier_id)
    page.wait_for_timeout(300)
    page.fill("input[name='sku']", sku)
    page.fill("input[name='quantity']", "1")
    page.fill("input[name='unit_price']", str(price))
    page.fill("input[name='name']", pname or sku)
    page.click("button[type='submit']")
    try:
        page.wait_for_url(re.compile(r"/web/purchase-orders/?$"), timeout=10000)
    except Exception:
        pass


def _extract_latest_po(page):
    page.goto(f"{BASE_URL}/web/purchase-orders")
    try:
        page.wait_for_selector("table tbody tr", timeout=10000)
    except Exception:
        return None, None
    rows = page.locator("table tbody tr")
    if rows.count() == 0:
        return None, None
    cells = rows.first.locator("td")
    po_number = cells.nth(0).locator("code").inner_text().strip() if cells.nth(0).locator("code").count() > 0 else ""
    eye_link = cells.nth(5).locator("a[href*='/web/purchase-orders/']") if cells.count() > 5 else None
    if eye_link is None or eye_link.count() == 0:
        eye_link = rows.first.locator("a[href*='/web/purchase-orders/']")
    if eye_link.count() > 0:
        href = eye_link.first.get_attribute("href") or ""
        m = re.search(r"/web/purchase-orders/([a-f0-9]{24})", href)
        if m:
            return m.group(1), po_number
    return None, None


def _create_goods_receipt(page, po_id, sku, pname):
    page.goto(f"{BASE_URL}/web/goods-receipt/create")
    page.wait_for_selector("select[name='po_id']")
    page.select_option("select[name='po_id']", value=po_id)
    page.wait_for_timeout(500)
    page.fill("input[name='sku']", sku)
    page.fill("input[name='quantity']", "1")
    page.fill("input[name='name']", pname or sku)
    page.click("button[type='submit']")
    try:
        page.wait_for_url(re.compile(r"/web/goods-receipt/?$"), timeout=10000)
    except Exception:
        pass


def _create_supplier_invoice(page, supplier_id, supplier_name, po_number, sku, pname, price):
    page.goto(f"{BASE_URL}/web/supplier-invoices/create")
    page.wait_for_selector("select[name='supplier_id']")
    page.select_option("select[name='supplier_id']", value=supplier_id)
    page.wait_for_timeout(300)
    if po_number:
        page.fill("input[name='po_number']", po_number)
    page.fill("input[name='sku']", sku)
    page.fill("input[name='quantity']", "1")
    page.fill("input[name='unit_price']", str(price))
    page.fill("input[name='name']", pname or sku)
    page.click("button[type='submit']")
    try:
        page.wait_for_url(re.compile(r"/web/supplier-invoices/?$"), timeout=10000)
    except Exception:
        pass


def _extract_latest_supplier_invoice(page):
    page.goto(f"{BASE_URL}/web/supplier-invoices")
    try:
        page.wait_for_selector("table tbody tr", timeout=10000)
    except Exception:
        return None, None
    rows = page.locator("table tbody tr")
    if rows.count() == 0:
        return None, None
    cells = rows.first.locator("td")
    invoice_number = cells.nth(0).locator("code").inner_text().strip() if cells.nth(0).locator("code").count() > 0 else ""
    total_text = cells.nth(4).inner_text().strip() if cells.count() > 4 else "0"
    total_val = 0.0
    try:
        total_val = float(total_text.replace(",", ""))
    except (ValueError, TypeError):
        m = re.search(r"([\d.]+)", total_text)
        if m:
            total_val = float(m.group(1))
    return invoice_number, total_val


def _create_payment(page, supplier_id, supplier_name, invoice_number, amount):
    page.goto(f"{BASE_URL}/web/payments/create")
    page.wait_for_selector("select[name='supplier_id']")
    page.select_option("select[name='supplier_id']", value=supplier_id)
    page.wait_for_timeout(300)
    if invoice_number:
        page.fill("input[name='invoice_number']", invoice_number)
    page.fill("input[name='amount']", str(amount))
    page.select_option("select[name='payment_method']", "bank_transfer")
    page.click("button[type='submit']")
    try:
        page.wait_for_url(re.compile(r"/web/payments/?$"), timeout=10000)
    except Exception:
        pass


def _process_company(company, n_cycles):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            _login(page, company["email"], "admin@123")
            page.wait_for_url(re.compile(r"/(web/dashboard|admin)/?"), timeout=15000)

            sku, pname = _get_first_product(page)
            if not sku:
                print(f"  [{company['name']}] SKIP \u2014 no products")
                return
            suffix = company["name"].split()[0] + str(random.randint(100, 999))
            supplier = _get_or_create_supplier(page, suffix)
            if not supplier:
                print(f"  [{company['name']}] SKIP \u2014 could not get/create supplier")
                return
            print(f"  [{company['name']}] SKU={sku}, Supplier={supplier['name']} id={supplier['id']}")

            for ci in range(1, n_cycles + 1):
                price = random.randint(50, 500)
                try:
                    print(f"    [{company['name']}] Cycle {ci}/{n_cycles}: creating PO...")
                    _create_po(page, supplier["id"], supplier["name"], sku, pname, price)

                    po_id, po_number = _extract_latest_po(page)
                    if not po_id:
                        print(f"    [{company['name']}] Cycle {ci}: FAIL \u2014 could not find PO id")
                        continue
                    print(f"    [{company['name']}] Cycle {ci}: PO id={po_id}, number={po_number}")

                    print(f"    [{company['name']}] Cycle {ci}: goods receipt...")
                    _create_goods_receipt(page, po_id, sku, pname)

                    print(f"    [{company['name']}] Cycle {ci}: supplier invoice...")
                    _create_supplier_invoice(page, supplier["id"], supplier["name"], po_number, sku, pname, price)

                    inv_number, inv_total = _extract_latest_supplier_invoice(page)
                    if not inv_number:
                        print(f"    [{company['name']}] Cycle {ci}: FAIL \u2014 could not find supplier invoice")
                        continue
                    print(f"    [{company['name']}] Cycle {ci}: Invoice number={inv_number}, total={inv_total}")

                    print(f"    [{company['name']}] Cycle {ci}: payment...")
                    _create_payment(page, supplier["id"], supplier["name"], inv_number, inv_total)

                    print(f"    \u2713 [{company['name']}] Cycle {ci} done")
                except Exception as e:
                    print(f"    \u2717 [{company['name']}] Cycle {ci} FAILED: {e}")

            print(f"  \u2713 [{company['name']}] completed {n_cycles} cycle(s)")
        except Exception as e:
            print(f"  \u2717 [{company['name']}] FAILED: {e}")
        finally:
            browser.close()


def main():
    n_cycles = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    n_companies = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    n_workers = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    print(f"P2P cycles per company: {n_cycles}, Companies: {n_companies}, Workers: {n_workers}")

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
                print(f"  {c['name']:35s} \u2192 {email}")
            else:
                print(f"  {c['name']:35s} \u2192 SKIP (no admin email)")

        browser.close()

    print(f"\nProcessing {len(enriched)} companies in parallel ({n_workers} workers)...")
    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        futures = {
            pool.submit(_process_company, c, n_cycles): c["name"]
            for c in enriched
        }
        for f in as_completed(futures):
            pass

    print("\nAll done.")


if __name__ == "__main__":
    main()
