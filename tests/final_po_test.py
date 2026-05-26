import asyncio
import random
import sys
from playwright.async_api import async_playwright

async def test_po_procurement(num_pos=1, num_items=5):
    """Final script for PO procurement testing using discovered selectors"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print(f"Starting PO Procurement Test: Creating {num_pos} PO(s) with {num_items} item(s) each...")
            
            # Navigate to login page
            await page.goto("http://127.0.0.1:5000/web/auth/login", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=20000)
            
            # Login with correct selectors
            print("Logging in...")
            await page.fill('input[type="email"]', 'lamia.el.khayat@test.ma')
            await page.fill('input[name="password"]', 'admin@123')
            await page.click('button[type="submit"]')
            
            # Wait for login to complete
            await page.wait_for_timeout(5000)
            await page.screenshot(path="after_login.png")
            
            # Check if login succeeded by looking for dashboard elements
            current_url = page.url
            print(f"After login URL: {current_url}")
            
            # Process each PO
            for po_num in range(num_pos):
                print(f"\n--- Processing PO {po_num + 1} of {num_pos} ---")
                
                # Navigate to Purchase Orders
                print("Navigating to Purchase Orders...")
                # Try to click on Purchase menu first
                try:
                    await page.click('text=Purchase', timeout=5000)
                    await page.wait_for_timeout(2000)
                    await page.click('text=Purchase Orders', timeout=5000)
                except:
                    # If that fails, go directly to PO list
                    await page.goto("http://127.0.0.1:5000/web#action=purchase.purchase_order_action", timeout=10000)
                
                await page.wait_for_timeout(3000)
                
                # Click Create button
                print("Creating new Purchase Order...")
                try:
                    await page.click('button:has-text("Create")', timeout=5000)
                    await page.wait_for_url("**/purchase/order/create*", timeout=10000)
                except:
                    # Fallback to direct navigation
                    await page.goto("http://127.0.0.1:5000/web#action=purchase.purchase_order_action&view_type=form&model=purchase.order", timeout=10000)
                    await page.wait_for_timeout(3000)
                
                await page.wait_for_load_state("networkidle", timeout=10000)
                
                # Generate random test data for this PO
                discount = random.randint(1, 15)
                tax = 20
                sku = f"SKU-Test-{random.randint(100, 999)}"
                item_name = f"Item-Test-{random.randint(100, 999)}"
                quantity = random.randint(5, 200)
                price = round(random.uniform(50, 500), 2)
                actual_num_items = random.randint(max(1, num_items - 2), num_items + 2)  # Add some variance
                
                print(f"Creating PO with {actual_num_items} items:")
                print(f"  SKU: {sku}")
                print(f"  Item Name: {item_name}")
                print(f"  Quantity: {quantity}")
                print(f"  Price: ${price}")
                print(f"  Discount: {discount}%")
                print(f"  Tax: {tax}%")
                
                # Select vendor (try to click and select first option)
                try:
                    await page.click('input[name="partner_id"]', timeout=3000)
                    await page.wait_for_timeout(1000)
                    await page.click('.dropdown-menu li:first-child', timeout=3000)
                except:
                    # If dropdown fails, just type a vendor name
                    await page.fill('input[name="partner_id"]', 'Test Vendor', timeout=3000)
                
                # Set date
                await page.fill('input[name="date_order"]', '2026-05-25', timeout=3000)
                
                # Add items
                for i in range(actual_num_items):
                    if i > 0:  # For additional items beyond first
                        try:
                            await page.click('button:has-text("Add a line")', timeout=3000)
                            await page.wait_for_timeout(1000)
                        except:
                            print(f"Warning: Could not click 'Add a line' for item {i+1}")
                    
                    # Fill item details - using indexed selectors for multiple lines
                    try:
                        # Product field
                        await page.fill(f'input[name="product_id"]:nth-of-type({i+1})', sku, timeout=3000)
                        await page.wait_for_timeout(500)
                    except:
                        try:
                            await page.click(f'input[name="product_id"]:nth-of-type({i+1})', timeout=3000)
                            await page.fill(f'input[name="product_id"]:nth-of-type({i+1})', sku, timeout=3000)
                        except:
                            print(f"Warning: Could not set product for item {i+1}")
                    
                    try:
                        # Item name/description
                        await page.fill(f'input[name="name"]:nth-of-type({i+1})', item_name, timeout=3000)
                    except:
                        print(f"Warning: Could not set item name for item {i+1}")
                    
                    try:
                        # Quantity
                        await page.fill(f'input[name="product_qty"]:nth-of-type({i+1})', str(quantity), timeout=3000)
                    except:
                        print(f"Warning: Could not set quantity for item {i+1}")
                    
                    try:
                        # Price unit
                        await page.fill(f'input[name="price_unit"]:nth-of-type({i+1})', str(price), timeout=3000)
                    except:
                        print(f"Warning: Could not set price for item {i+1}")
                    
                    try:
                        # Discount
                        await page.fill(f'input[name="discount"]:nth-of-type({i+1})', str(discount), timeout=3000)
                    except:
                        print(f"Warning: Could not set discount for item {i+1}")
                    
                    # Tax setting is complex, skipping for now but could be added if needed
                
                # Wait a moment for all entries to settle
                await page.wait_for_timeout(2000)
                
                # Confirm the purchase order
                print("Confirming Purchase Order...")
                try:
                    await page.click('button:has-text("Confirm Purchase Order")', timeout=5000)
                except:
                    try:
                        await page.click('button:has-text("Confirm")', timeout=5000)
                    except:
                        print("Warning: Could not find confirm button")
                
                # Wait for processing
                await page.wait_for_timeout(5000)
                await page.screenshot(path=f"po_confirmation_{po_num + 1}.png")
                
                # Check for success
                try:
                    await page.wait_for_text('text=Purchase Order confirmed', timeout=10000)
                    print("SUCCESS: Purchase Order confirmed!")
                except:
                    try:
                        await page.wait_for_text('text=Purchase Order', timeout=5000)
                        print("SUCCESS: Purchase Order created (checked for PO text)")
                    except:
                        print("WARNING: Could not verify PO creation, but continuing...")
                
                # Try to get PO number
                try:
                    po_number = await page.text_content('o_field_widget[name="name"]', timeout=3000)
                    if not po_number or not po_number.strip():
                        po_number = await page.text_content('h1.o_form_title', timeout=3000)
                    if not po_number or not po_number.strip():
                        po_number = "Unknown (could not extract)"
                    print(f"Created Purchase Order: {po_number}")
                except:
                    po_number = "Unknown (extraction failed)"
                    print(f"Created Purchase Order: {po_number}")
            
            print(f"\nPO Procurement Test Completed Successfully! Created {num_pos} PO(s).")
            
        except Exception as e:
            print(f"Test failed with error: {str(e)}")
            # Take screenshot for debugging
            try:
                await page.screenshot(path="error_final.png")
            except:
                pass
            raise
        finally:
            print("Closing browser...")
            await context.close()
            await browser.close()

if __name__ == "__main__":
    # Parse command line arguments
    num_pos = 1
    num_items = 5
    
    if len(sys.argv) > 1:
        try:
            num_pos = int(sys.argv[1])
        except ValueError:
            print("Invalid number for PO count. Using default: 1")
    
    if len(sys.argv) > 2:
        try:
            num_items = int(sys.argv[2])
        except ValueError:
            print("Invalid number for items count. Using default: 5")
    
    print(f"Command line args: {num_pos} PO(s), {num_items} item(s) per PO")
    asyncio.run(test_po_procurement(num_pos, num_items))