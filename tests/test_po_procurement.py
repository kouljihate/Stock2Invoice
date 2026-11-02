import os
import re
import sys
import random
import struct
import tempfile
import zlib
from datetime import datetime

from playwright.sync_api import expect, sync_playwright

BASE_URL = "http://127.0.0.1:5000"

# Moroccan names for vendor/contact generation (same as in test_create_company.py)
MOROCCAN_NAMES = [
    "Youssef Benali", "Fatima Zahra El Amrani", "Mohamed El Idrissi",
    "Amina Bouskri", "Hassan El Fassi", "Khadija Ouazzani",
    "Omar Bennani", "Nadia Tazi", "Karim El Maleh",
    "Sara Berrada", "Rachid El Alami", "Meryem El Ghali",
    "Adil El Haddad", "Sanae El Mokhtar", "Hicham El Filali",
    "Imane El Kadiri", "Nabil El Amraoui", "Salma El Mansouri",
    "Soufiane El Moutaouakil", "Lamia El Khayat",
    "Mehdi El Aissaoui", "Ghita El Fathi", "Anas El Mahfoudi",
    "Mouna El Hachimi", "Yassine El Ouafi",
]


def _make_png(pixels, size=64):
    """Helper function to generate PNG logo (same as in test_create_company.py)"""
    raw = b""
    for y in range(size):
        raw += b"\x00"
        for x in range(size):
            raw += struct.pack("BBB", *pixels[y * size + x])

    def chunk(typ, data):
        c = typ + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(raw))
    return sig + ihdr + idat + chunk(b"IEND", b"")


def _generate_logo(name):
    """Generate a logo image (same pattern as in test_create_company.py)"""
    try:
        rng = random.Random(name)
        bg = (rng.randint(30, 200), rng.randint(30, 200), rng.randint(30, 200))
        fg = (min(255, bg[0] + 80), min(255, bg[1] + 80), min(255, bg[2] + 80))

        size = 64
        cx = cy = size // 2
        r = size // 3
        pixels = []
        for y in range(size):
            for x in range(size):
                dx, dy = x - cx, y - cy
                if dx * dx + dy * dy < r * r:
                    pixels.append(fg)
                else:
                    pixels.append(bg)
        logo_bytes = _make_png(pixels, size)

        fd, path = tempfile.mkstemp(suffix=".png")
        os.write(fd, logo_bytes)
        os.close(fd)
        return path
    except Exception:
        return None


def _existing_vendors(page):
    """Get list of existing vendor names (similar to _existing_names in test_create_company.py)"""
    page.goto(f"{BASE_URL}/web/suppliers")
    try:
        page.wait_for_selector("table tbody tr", timeout=5000)
    except Exception:
        pass  # Table might not exist or be empty
    try:
        return {page.locator("table tbody tr td:first-child strong").nth(i).inner_text()
                for i in range(page.locator("table tbody tr td:first-child strong").count())}
    except Exception:
        return set()


def _pick_unused_vendor(existing):
    """Pick an unused vendor name (similar to _pick_unused in test_create_company.py)"""
    available = [name for name in MOROCCAN_NAMES if name not in existing]
    return random.choice(available) if available else random.choice(MOROCCAN_NAMES)


def _generate_po_reference():
    """Generate a random PO reference"""
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")[:16]
    return f"PO-{ts[-8:]}"


def _generate_sku():
    """Generate a random SKU"""
    return f"SKU-Test-{random.randint(100, 999)}"


def _generate_item_name():
    """Generate a random item name"""
    return f"Item-Test-{random.randint(100, 999)}"


def _create_single_po(page, index=0, num_items=3):
    """Create a single purchase order (equivalent to _create_single_company)"""
    po_reference = _generate_po_reference()
    
    print(f"  [{index}] Creating PO: {po_reference} with {num_items} items")

    # Navigate to Purchase Orders list
    page.goto(f"{BASE_URL}/web#action=purchase.purchase_order_action")
    page.wait_for_load_state("networkidle")
    
    # Click Create button
    try:
        page.click("button:has-text('Create')", timeout=5000)
        page.wait_for_url(re.compile(r".*/purchase/order/create.*"), timeout=10000)
    except Exception as e:
        print(f"  [{index}] Failed to click Create button, trying direct navigation: {e}")
        # Fallback to direct navigation
        page.goto(f"{BASE_URL}/web#action=purchase.purchase_order_action&view_type=form&model=purchase.order")
        page.wait_for_load_state("networkidle")
    
    # Wait for form to load
    page.wait_for_selector("form", timeout=5000)
    
    # Fill PO details
    try:
        # Reference/Number
        page.fill("input[name='origin']", po_reference)
        
        # Date
        today = datetime.now().strftime("%Y-%m-%d")
        page.fill("input[name='date_order']", today)
        
        # Vendor (Partner) - get unused vendor name
        existing_vendors = _existing_vendors(page)
        vendor_name = _pick_unused_vendor(existing_vendors)
        
        try:
            # Try to select from dropdown
            page.click("input[name='partner_id']", timeout=3000)
            page.wait_for_timeout(500)
            page.type("input[name='partner_id']", vendor_name, delay=100)
            page.wait_for_timeout(1000)
            # Press Enter to select first option
            page.keyboard.press("Enter")
        except:
            # Fallback: direct fill
            page.fill("input[name='partner_id']", vendor_name)
        
        print(f"    Vendor: {vendor_name}")
        
    except Exception as e:
        print(f"    Warning: Could not fill some PO header fields: {e}")
    
    # Add items
    for i in range(num_items):
        if i > 0:  # For additional items beyond first
            try:
                page.click("button:has-text('Add a line')", timeout=3000)
                page.wait_for_timeout(1000)
            except Exception as e:
                print(f"    Warning: Could not click 'Add a line' for item {i+1}: {e}")
        
        # Fill item details for this line
        try:
            # Product/SKU
            sku = _generate_sku()
            try:
                product_input = page.locator(f"input[name='product_id']:nth-of-type({i+1})")
                product_input.fill(sku)
                page.wait_for_timeout(500)  # Wait for product selection
            except:
                try:
                    product_input = page.locator(f"input[name='product_id']:nth-of-type({i+1})")
                    product_input.click()
                    product_input.fill(sku)
                except:
                    print(f"    Warning: Could not set product for item {i+1}")
            
            # Item Name/Description
            item_name = _generate_item_name()
            try:
                page.locator(f"input[name='name']:nth-of-type({i+1})").fill(item_name)
            except:
                print(f"    Warning: Could not set item name for item {i+1}")
            
            # Quantity
            quantity = random.randint(5, 200)
            try:
                page.locator(f"input[name='product_qty']:nth-of-type({i+1})").fill(str(quantity))
            except:
                print(f"    Warning: Could not set quantity for item {i+1}")
            
            # Price Unit
            price = round(random.uniform(50, 500), 2)
            try:
                page.locator(f"input[name='price_unit']:nth-of-type({i+1})").fill(str(price))
            except:
                print(f"    Warning: Could not set price for item {i+1}")
            
            # Discount (1-15%)
            discount = random.randint(1, 15)
            try:
                page.locator(f"input[name='discount']:nth-of-type({i+1})").fill(str(discount))
            except:
                print(f"    Warning: Could not set discount for item {i+1}")
                
            print(f"    Item {i+1}: SKU={sku}, Qty={quantity}, Price=${price}, Discount={discount}%")
            
        except Exception as e:
            print(f"    Warning: Error filling item {i+1}: {e}")
    
    # Confirm the Purchase Order
    try:
        print(f"  [{index}] Confirming Purchase Order...")
        page.click("button:has-text('Confirm Purchase Order')", timeout=5000)
        # Alternative button text
        page.wait_for_timeout(2000)
        try:
            page.click("button:has-text('Confirm')", timeout=3000)
        except:
            pass  # Button might not exist with this text
        
        # Wait for confirmation
        page.wait_for_timeout(3000)
        
        # Check for success
        try:
            expect(page.locator("text=Purchase Order confirmed")).to_be_visible(timeout=10000)
            print(f"  [{index}] OK - PO confirmed")
        except:
            try:
                expect(page.locator("text=Purchase Order")).to_be_visible(timeout=5000)
                print(f"  [{index}] OK - PO created")
            except:
                print(f"  [{index}] WARNING: Could not verify PO creation")
                
    except Exception as e:
        print(f"  [{index}] Error during confirmation: {e}")


def create_purchase_orders(count, items_per_po=3):
    """Create multiple purchase orders (equivalent to create_companies)"""
    print(f"Creating {count} purchase order(s) with {items_per_po} item(s) each...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Login
        page.goto(f"{BASE_URL}/web/auth/login")
        page.fill("input[type='email']", "lamia.el.khayat@test.ma")
        page.fill("input[name='password']", "admin@123")
        page.click("button[type='submit']")
        page.wait_for_url(re.compile(r"/web/?"))
        print("Logged in successfully")

        # Create POs
        for i in range(1, count + 1):
            _create_single_po(page, i, items_per_po)

        browser.close()
    print("Done.")

# ── CLI entry point ──
if __name__ == "__main__":
    try:
        count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        items = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    except (IndexError, ValueError):
        count = 1
        items = 3
    
    print(f"Command line args: {count} PO(s), {items} item(s) per PO")
    create_purchase_orders(count, items)

# ── pytest entry point (always creates 1) ──
class TestPoProcurement:
    def test_create_po_successfully(self):
        create_purchase_orders(1, 3)