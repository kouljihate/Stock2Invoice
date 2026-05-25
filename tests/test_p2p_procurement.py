import re
import sys
import time
import random
import string

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"


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


def main():
    email = "lamia.el.khayat@test.ma"
    password = "admin@123"

    print("=" * 60)
    print("P2P Procurement Test Scenario")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 800})

        page.on("dialog", lambda dialog: dialog.accept())

        # ----------------------------------------------------------------
        # Step 1: Login
        # ----------------------------------------------------------------
        print("\n[Step 1] Login using lamia.el.khayat@test.ma")
        _login(page, email, password)
        print("    Logged in successfully")

        # ----------------------------------------------------------------
        # Ensure at least one supplier exists for this company
        # ----------------------------------------------------------------
        print("\n    Ensuring supplier exists...")
        supplier_id = _ensure_supplier_exists(page)
        if not supplier_id:
            print("    ERROR: Could not get/create supplier")
            browser.close()
            sys.exit(1)

        # ----------------------------------------------------------------
        # Step 2-3: Goto P2P -> PO -> Add PO
        # ----------------------------------------------------------------
        print("\n[Step 2-3] Goto P2P -> PO -> Add PO")
        _navigate(page, f"{BASE_URL}/web/purchase-orders/create", "PO creation form")
        page.wait_for_selector("select[name='supplier_id']")
        page.wait_for_timeout(500)

        # ----------------------------------------------------------------
        # Step 4: Fill All Fields
        # ----------------------------------------------------------------
        print("\n[Step 4] Fill All Fields (1st supplier, random, Tax=21%)")

        # Select 1st supplier (index 1, since index 0 is "-- Select Supplier --")
        supplier_options = page.locator("select[name='supplier_id'] option")
        option_count = supplier_options.count()
        if option_count < 2:
            print("    ERROR: No suppliers available in dropdown!")
            browser.close()
            sys.exit(1)
        page.select_option("select[name='supplier_id']", index=1)
        page.wait_for_timeout(300)
        supplier_name = supplier_options.nth(1).inner_text()
        print(f"    Selected supplier: {supplier_name}")

        discount = round(random.uniform(0, 10), 2)
        tax = 21.0
        sku = "SKU-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        item_name = "Item " + ''.join(random.choices(string.ascii_uppercase, k=4))
        qty = random.randint(1, 10)
        price = round(random.uniform(50, 500), 2)
        notes = "Test " + ''.join(random.choices(string.ascii_letters, k=10))

        page.fill("input[name='discount_percent']", str(discount))
        page.fill("input[name='tax_percent']", str(tax))
        page.fill("input[name='sku']", sku)
        page.fill("input[name='name']", item_name)
        page.fill("input[name='quantity']", str(qty))
        page.fill("input[name='unit_price']", str(price))
        page.fill("textarea[name='notes']", notes)
        print(f"    Tax={tax}%, Discount={discount}%, SKU={sku}, Qty={qty}, Price={price}")

        # Click "Create Purchase Order" button
        page.click("button[type='submit']:has-text('Create Purchase Order')")
        try:
            page.wait_for_url(re.compile(r"/web/purchase-orders/?$"), timeout=10000)
        except Exception:
            page.wait_for_timeout(3000)
        print(f"    PO created, redirect to: {page.url}")

        # ----------------------------------------------------------------
        # Step 5: Click Send button and confirm popup
        # ----------------------------------------------------------------
        print("\n[Step 5] Send PO to Supplier")
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
            print("    Send button clicked, popup accepted")
        else:
            print("    WARNING: Send button not found!")

        # ----------------------------------------------------------------
        # Step 6: Check if PO status is "sent"
        # ----------------------------------------------------------------
        print("\n[Step 6] Check PO status = sent")
        try:
            page.wait_for_selector("table tbody tr", timeout=5000)
        except Exception:
            page.wait_for_timeout(2000)
        status_badge = page.locator("table tbody tr").first.locator("span.badge")
        po_status = status_badge.inner_text().strip().lower()
        print(f"    PO status: {po_status}")
        if po_status != "sent":
            print(f"    ERROR: Expected 'sent', got '{po_status}'")
            browser.close()
            sys.exit(1)
        print("    [OK] PO status is 'sent'")

        # ----------------------------------------------------------------
        # Step 7: Goto Goods Receipt
        # ----------------------------------------------------------------
        print("\n[Step 7] Goto Goods Receipt")
        _navigate(page, f"{BASE_URL}/web/goods-receipt", "Goods Receipt list")

        # ----------------------------------------------------------------
        # Step 8: Wait 3 seconds
        # ----------------------------------------------------------------
        print("\n[Step 8] Wait 3 seconds")
        page.wait_for_timeout(3000)

        # ----------------------------------------------------------------
        # Step 9: Click "Mark PO Received" and confirm popup
        # ----------------------------------------------------------------
        print("\n[Step 9] Mark PO Received")
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
            print("    Mark PO Received button clicked, popup accepted")
        else:
            print("    WARNING: Mark PO Received button not found!")

        # ----------------------------------------------------------------
        # Step 10: Check GR status is "received"
        # ----------------------------------------------------------------
        print("\n[Step 10] Check GR status = received")
        try:
            page.wait_for_selector("table tbody tr", timeout=5000)
        except Exception:
            page.wait_for_timeout(2000)
        status_badge = page.locator("table tbody tr").first.locator("span.badge")
        gr_status = status_badge.inner_text().strip().lower()
        print(f"    GR status: {gr_status}")
        if gr_status != "received":
            print(f"    ERROR: Expected 'received', got '{gr_status}'")
            browser.close()
            sys.exit(1)
        print("    [OK] GR status is 'received'")

        # ----------------------------------------------------------------
        # Step 11: Goto Supplier Invoices
        # ----------------------------------------------------------------
        print("\n[Step 11] Goto Supplier Invoices")
        _navigate(page, f"{BASE_URL}/web/supplier-invoices", "Supplier Invoices list")

        # ----------------------------------------------------------------
        # Step 12: Check if status is "draft"
        # ----------------------------------------------------------------
        print("\n[Step 12] Check SI status = draft")
        try:
            page.wait_for_selector("table tbody tr", timeout=5000)
        except Exception:
            page.wait_for_timeout(2000)
        status_badge = page.locator("table tbody tr").first.locator("span.badge")
        si_status = status_badge.inner_text().strip().lower()
        print(f"    Invoice status: {si_status}")
        if si_status != "draft":
            print(f"    ERROR: Expected 'draft', got '{si_status}'")
            browser.close()
            sys.exit(1)
        print("    [OK] Invoice status is 'draft'")

        # ----------------------------------------------------------------
        # Step 13: Click validate button and confirm popup
        # ----------------------------------------------------------------
        print("\n[Step 13] Validate invoice")
        validate_btn = page.locator("button[title='Validate']")
        if validate_btn.count() == 0:
            validate_btn = page.locator("form button i.bi-check-circle")
        if validate_btn.count() > 0:
            validate_btn.first.click()
            page.wait_for_timeout(1000)
            print("    Validate button clicked, popup accepted")
        else:
            print("    WARNING: Validate button not found!")

        # ----------------------------------------------------------------
        # Step 14: Check if status becomes "approved"
        # ----------------------------------------------------------------
        print("\n[Step 14] Check SI status = approved")
        try:
            page.wait_for_selector("table tbody tr", timeout=5000)
        except Exception:
            page.wait_for_timeout(2000)
        status_badge = page.locator("table tbody tr").first.locator("span.badge")
        si_status = status_badge.inner_text().strip().lower()
        print(f"    Invoice status: {si_status}")
        if si_status != "approved":
            print(f"    ERROR: Expected 'approved', got '{si_status}'")
            browser.close()
            sys.exit(1)
        print("    [OK] Invoice status is 'approved'")

        # ----------------------------------------------------------------
        # Step 15: Goto Payments
        # ----------------------------------------------------------------
        print("\n[Step 15] Goto Payments")
        _navigate(page, f"{BASE_URL}/web/payments", "Payments list")

        # ----------------------------------------------------------------
        # Step 16: Check if status is "pending"
        # ----------------------------------------------------------------
        print("\n[Step 16] Check Payment status = pending")
        try:
            page.wait_for_selector("table tbody tr", timeout=5000)
        except Exception:
            page.wait_for_timeout(2000)
        status_badge = page.locator("table tbody tr").first.locator("span.badge")
        payment_status = status_badge.inner_text().strip().lower()
        print(f"    Payment status: {payment_status}")
        if payment_status != "pending":
            print(f"    ERROR: Expected 'pending', got '{payment_status}'")
            browser.close()
            sys.exit(1)
        print("    [OK] Payment status is 'pending'")

        # ----------------------------------------------------------------
        # All done
        # ----------------------------------------------------------------
        print("\n" + "=" * 60)
        print("[OK] All steps completed successfully!")
        print("=" * 60)

        browser.close()


if __name__ == "__main__":
    main()
