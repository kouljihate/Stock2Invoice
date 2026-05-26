import asyncio
import sys
from playwright.async_api import async_playwright

async def test_po_procurement(num_pos=1, num_items=2):
    """Minimal script for PO procurement testing"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print(f"Starting PO Procurement Test: Creating {num_pos} PO(s) with {num_items} item(s) each...")
            
            # Navigate to login page
            await page.goto("http://127.0.0.1:5000/web/auth/login", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=20000)
            
            # Login with correct selectors (based on our debug findings)
            print("Logging in...")
            await page.fill('input[type="email"]', 'lamia.el.khayat@test.ma')
            await page.fill('input[name="password"]', 'admin@123')
            await page.click('button[type="submit"]')
            
            # Wait for login to complete
            await page.wait_for_timeout(5000)
            
            # Check if login succeeded
            current_url = page.url
            print(f"After login URL: {current_url}")
            
            if '/web/auth/login' in current_url:
                print("ERROR: Still on login page after submitting credentials")
                await page.screenshot(path="login_failed.png")
                return
            
            print("Login successful!")
            
            # Navigate to Purchase Orders
            print("Navigating to Purchase Orders...")
            try:
                # Try direct navigation to PO list
                await page.goto("http://127.0.0.1:5000/web#action=purchase.purchase_order_action", timeout=10000)
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"Direct navigation failed: {e}")
                # Try clicking through menus
                try:
                    await page.click('text=Purchase', timeout=5000)
                    await page.wait_for_timeout(2000)
                    await page.click('text=Purchase Orders', timeout=5000)
                    await page.wait_for_timeout(3000)
                except Exception as e2:
                    print(f"Menu navigation also failed: {e2}")
            
            # Click Create button
            print("Creating new Purchase Order...")
            try:
                await page.click('button:has-text("Create")', timeout=5000)
                await page.wait_for_url("**/purchase/order/create*", timeout=10000)
                print("Successfully navigated to PO creation form")
            except Exception as e:
                print(f"Clicking Create button failed: {e}")
                # Try direct navigation to form
                try:
                    await page.goto("http://127.0.0.1:5000/web#action=purchase.purchase_order_action&view_type=form&model=purchase.order", timeout=10000)
                    await page.wait_for_timeout(3000)
                    print("Used direct navigation to PO form")
                except Exception as e2:
                    print(f"Direct navigation to form also failed: {e2}")
            
            await page.wait_for_load_state("networkidle", timeout=10000)
            await page.screenshot(path="po_form.png")
            
            # Try to fill in basic fields
            print("Attempting to fill PO form...")
            
            # Try to find and fill vendor field
            try:
                await page.fill('input[name="partner_id"]', 'Test Vendor', timeout=5000)
                print("Successfully filled vendor field")
            except Exception as e:
                print(f"Could not fill vendor field: {e}")
                # Try clicking and typing
                try:
                    await page.click('input[name="partner_id"]', timeout=3000)
                    await page.fill('input[name="partner_id"]', 'Test Vendor', timeout=3000)
                    print("Successfully filled vendor field via click+type")
                except Exception as e2:
                    print(f"Could not fill vendor field via click+type: {e2}")
            
            # Try to set date
            try:
                await page.fill('input[name="date_order"]', '2026-05-25', timeout=3000)
                print("Successfully filled date field")
            except Exception as e:
                print(f"Could not fill date field: {e}")
            
            print("Test completed - check screenshots for results")
            
        except Exception as e:
            print(f"Test failed with error: {str(e)}")
            # Take screenshot for debugging
            try:
                await page.screenshot(path="error_minimal.png")
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
    num_items = 2
    
    if len(sys.argv) > 1:
        try:
            num_pos = int(sys.argv[1])
        except ValueError:
            print("Invalid number for PO count. Using default: 1")
    
    if len(sys.argv) > 2:
        try:
            num_items = int(sys.argv[2])
        except ValueError:
            print("Invalid number for items count. Using default: 2")
    
    print(f"Command line args: {num_pos} PO(s), {num_items} item(s) per PO")
    asyncio.run(test_po_procurement(num_pos, num_items))