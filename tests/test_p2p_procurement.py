import os
import re
import sys
import time
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"


def _fetch_random_users(count):
    os.environ["MONGO_URI"] = "mongodb://localhost:27017/stockinvoice"
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)
    from app import create_app
    from app.extensions.db import mongo

    app = create_app()
    with app.app_context():
        all_users = list(mongo.db.users.find({"email": {"$ne": "admin@si.ma"}}, {"email": 1}))
        if not all_users:
            print("No non-admin users found in DB!")
            return []
        selected = random.sample(all_users, min(count, len(all_users)))
        return [u["email"] for u in selected]


def _login(page, email, password):
    page.goto(f"{BASE_URL}/web/auth/login")
    page.wait_for_selector("input[name='email']")
    page.fill("input[name='email']", email)
    page.fill("input[name='password']", password)
    page.click("button[type='submit']")
    try:
        page.wait_for_url(re.compile(r"/(web/dashboard|admin)/?"), timeout=15000)
    except Exception:
        page.wait_for_timeout(3000)


def _navigate(page, url, description=""):
    print(f"    Navigating to {description}...")
    page.goto(url)
    page.wait_for_load_state("networkidle")


def _ensure_supplier_exists(page):
    page.goto(f"{BASE_URL}/web/suppliers")
    page.wait_for_load_state("networkidle")
    try:
        page.wait_for_selector("table tbody tr", timeout=5000)
        rows = page.locator("table tbody tr")
        if rows.count() > 0 and rows.first.locator("td").count() > 1:
            first_name = rows.first.locator("td").nth(0).locator("strong")
            if first_name.count() > 0 and first_name.inner_text().strip():
                print(f"    Found existing supplier: {first_name.inner_text().strip()}")
                href = rows.first.locator("a[href*='/web/suppliers/']").first.get_attribute("href") or ""
                m = re.search(r"/web/suppliers/([a-f0-9]{24})", href)
                if m:
                    return m.group(1)
    except Exception:
        pass

    suffix = random.randint(100, 9999)
    name = f"Test Supplier {suffix}"
    print(f"    Creating supplier: {name}")
    page.goto(f"{BASE_URL}/web/suppliers/create")
    page.wait_for_selector("input[name='name']")
    page.fill("input[name='name']", name)
    page.fill("input[name='contact_name']", f"Contact {suffix}")
    page.fill("input[name='email']", f"sup.{suffix}@test.ma")
    page.fill("input[name='phone']", f"+212 6{random.randint(10,99)}{random.randint(10,99)}{random.randint(10,99)}{random.randint(10,99)}")
    page.fill("input[name='city']", random.choice(["Casablanca", "Rabat", "Marrakech", "Fes", "Tanger"]))
    page.fill("input[name='payment_terms']", "Net 30")
    page.click("button[type='submit']")
    try:
        page.wait_for_url(re.compile(r"/web/suppliers/?$"), timeout=8000)
    except Exception:
        page.wait_for_timeout(2000)

    page.goto(f"{BASE_URL}/web/suppliers")
    page.wait_for_load_state("networkidle")
    try:
        page.wait_for_selector("table tbody tr", timeout=5000)
    except Exception:
        pass
    rows = page.locator("table tbody tr")
    for i in range(rows.count()):
        name_el = rows.nth(i).locator("td").nth(0).locator("strong")
        if name_el.count() > 0 and name_el.inner_text().strip() == name:
            href = rows.nth(i).locator("a[href*='/web/suppliers/']").first.get_attribute("href") or ""
            m = re.search(r"/web/suppliers/([a-f0-9]{24})", href)
            if m:
                print(f"    Supplier created: {name} (id: {m.group(1)})")
                return m.group(1)
    return None


def _run_scenario(email, password, idx):
    label = f"[User {idx}: {email}]"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 800})
            page.on("dialog", lambda dialog: dialog.accept())

            # Step 1: Login
            print(f"\n{label} Step 1: Login")
            _login(page, email, password)
            print(f"    {label} Logged in")

            # Ensure supplier exists
            print(f"    {label} Ensuring supplier...")
            _ensure_supplier_exists(page)

            # Step 2-3: Goto PO create
            print(f"    {label} Step 2-3: Goto PO create")
            _navigate(page, f"{BASE_URL}/web/purchase-orders/create", "PO creation")
            page.wait_for_selector("select[name='supplier_id']")
            page.wait_for_timeout(500)

            # Step 4: Fill fields
            print(f"    {label} Step 4: Fill fields")
            supplier_options = page.locator("select[name='supplier_id'] option")
            if supplier_options.count() < 2:
                print(f"    {label} ERROR: No suppliers")
                browser.close()
                return False
            page.select_option("select[name='supplier_id']", index=1)
            page.wait_for_timeout(300)

            discount = round(random.uniform(0, 10), 2)
            tax = 21.0
            sku = "SKU-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            item_name = "Item " + "".join(random.choices(string.ascii_uppercase, k=4))
            qty = random.randint(1, 10)
            price = round(random.uniform(50, 500), 2)
            notes = "Test " + "".join(random.choices(string.ascii_letters, k=10))

            page.fill("input[name='discount_percent']", str(discount))
            page.fill("input[name='tax_percent']", str(tax))
            page.fill("input[name='sku']", sku)
            page.fill("input[name='name']", item_name)
            page.fill("input[name='quantity']", str(qty))
            page.fill("input[name='unit_price']", str(price))
            page.fill("textarea[name='notes']", notes)

            page.click("button[type='submit']:has-text('Create Purchase Order')")
            try:
                page.wait_for_url(re.compile(r"/web/purchase-orders/?$"), timeout=10000)
            except Exception:
                page.wait_for_timeout(3000)

            # Step 5: Send PO
            print(f"    {label} Step 5: Send PO")
            try:
                page.wait_for_selector("table tbody tr", timeout=5000)
            except Exception:
                page.wait_for_timeout(2000)
            send_btn = page.locator("button[title='Send']")
            if send_btn.count() == 0:
                send_btn = page.locator("form button i.bi-send")
            if send_btn.count() > 0:
                send_btn.first.click()
                page.wait_for_timeout(1000)

            # Step 6: Check PO status
            print(f"    {label} Step 6: Check PO status")
            try:
                page.wait_for_selector("table tbody tr", timeout=5000)
            except Exception:
                page.wait_for_timeout(2000)
            po_status = page.locator("table tbody tr").first.locator("span.badge").inner_text().strip().lower()
            if po_status != "sent":
                print(f"    {label} FAIL: PO status {po_status} != sent")
                browser.close()
                return False
            print(f"    {label} [OK] PO is sent")

            # Step 7-8: Goto GR, wait 3s
            print(f"    {label} Step 7-8: Goto GR + wait")
            _navigate(page, f"{BASE_URL}/web/goods-receipt", "GR list")
            page.wait_for_timeout(3000)

            # Step 9: Mark PO Received
            print(f"    {label} Step 9: Mark PO Received")
            try:
                page.wait_for_selector("table tbody tr", timeout=5000)
            except Exception:
                page.reload()
                page.wait_for_selector("table tbody tr", timeout=5000)
            mark_btn = page.locator("button[title='Mark PO Received']")
            if mark_btn.count() == 0:
                mark_btn = page.locator("form button i.bi-check-lg")
            if mark_btn.count() > 0:
                mark_btn.first.click()
                page.wait_for_timeout(1000)

            # Step 10: Check GR status
            print(f"    {label} Step 10: Check GR status")
            try:
                page.wait_for_selector("table tbody tr", timeout=5000)
            except Exception:
                page.wait_for_timeout(2000)
            gr_status = page.locator("table tbody tr").first.locator("span.badge").inner_text().strip().lower()
            if gr_status != "received":
                print(f"    {label} FAIL: GR status {gr_status} != received")
                browser.close()
                return False
            print(f"    {label} [OK] GR is received")

            # Step 11-12: Goto SI, check draft
            print(f"    {label} Step 11-12: Goto SI")
            _navigate(page, f"{BASE_URL}/web/supplier-invoices", "SI list")
            try:
                page.wait_for_selector("table tbody tr", timeout=5000)
            except Exception:
                page.wait_for_timeout(2000)
            si_status = page.locator("table tbody tr").first.locator("span.badge").inner_text().strip().lower()
            if si_status != "draft":
                print(f"    {label} FAIL: SI status {si_status} != draft")
                browser.close()
                return False
            print(f"    {label} [OK] SI is draft")

            # Step 13: Validate
            print(f"    {label} Step 13: Validate invoice")
            validate_btn = page.locator("button[title='Validate']")
            if validate_btn.count() == 0:
                validate_btn = page.locator("form button i.bi-check-circle")
            if validate_btn.count() > 0:
                validate_btn.first.click()
                page.wait_for_timeout(1000)

            # Step 14: Check approved
            print(f"    {label} Step 14: Check approved")
            try:
                page.wait_for_selector("table tbody tr", timeout=5000)
            except Exception:
                page.wait_for_timeout(2000)
            si_status = page.locator("table tbody tr").first.locator("span.badge").inner_text().strip().lower()
            if si_status != "approved":
                print(f"    {label} FAIL: SI status {si_status} != approved")
                browser.close()
                return False
            print(f"    {label} [OK] SI is approved")

            # Step 15-16: Goto Payments, check pending
            print(f"    {label} Step 15-16: Goto Payments")
            _navigate(page, f"{BASE_URL}/web/payments", "Payments list")
            try:
                page.wait_for_selector("table tbody tr", timeout=5000)
            except Exception:
                page.wait_for_timeout(2000)
            payment_status = page.locator("table tbody tr").first.locator("span.badge").inner_text().strip().lower()
            if payment_status != "pending":
                print(f"    {label} FAIL: Payment status {payment_status} != pending")
                browser.close()
                return False
            print(f"    {label} [OK] Payment is pending")

            print(f"\n{label} [OK] All steps completed!")
            browser.close()
            return True
    except Exception as e:
        print(f"    {label} EXCEPTION: {e}")
        return False


def main():
    n_users = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    password = "admin@123"

    print("=" * 60)
    print(f"P2P Procurement - {n_users} simultaneous user(s)")
    print("=" * 60)

    print("\nFetching random users from MongoDB...")
    emails = _fetch_random_users(n_users)
    if not emails:
        print("ERROR: No users found in database!")
        sys.exit(1)

    print(f"Selected users: {', '.join(emails)}")

    print(f"\nRunning {len(emails)} scenario(s) in parallel...")
    with ThreadPoolExecutor(max_workers=len(emails)) as pool:
        futures = {
            pool.submit(_run_scenario, email, password, i + 1): email
            for i, email in enumerate(emails)
        }
        results = []
        for f in as_completed(futures):
            email = futures[f]
            ok = f.result()
            results.append((email, ok))
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {email}")

    passed = sum(1 for _, ok in results if ok)
    failed = len(results) - passed
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(results)}")
    print("=" * 60)
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
