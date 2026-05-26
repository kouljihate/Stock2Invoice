import asyncio
from playwright.async_api import async_playwright

async def simple_test():
    """A simple test to verify we can reach the application and take screenshots"""
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("Navigating to login page...")
            await page.goto("http://127.0.0.1:5000/web/auth/login", timeout=30000)
            
            print("Waiting for page to load...")
            await page.wait_for_load_state("networkidle", timeout=20000)
            
            # Take screenshot of login page
            await page.screenshot(path="login_page_debug.png")
            print("Login page screenshot saved")
            
            # Check if we can see common login elements
            title = await page.title()
            print(f"Page title: {title}")
            
            # Try to find login elements
            login_input = await page.query_selector('input#login, input[name="login"]')
            password_input = await page.query_selector('input#password, input[name="password"]')
            submit_button = await page.query_selector('button[type="submit"], .btn-primary')
            
            print(f"Login input found: {login_input is not None}")
            print(f"Password input found: {password_input is not None}")
            print(f"Submit button found: {submit_button is not None}")
            
            # If we found the elements, try to fill them
            if login_input and password_input:
                print("Filling login credentials...")
                await login_input.fill('lamia.el.khayat@test.ma')
                await password_input.fill('admin@123')
                
                if submit_button:
                    print("Clicking submit...")
                    await submit_button.click()
                    
                    # Wait a bit for response
                    await page.wait_for_timeout(5000)
                    
                    # Take screenshot after login attempt
                    await page.screenshot(path="after_login_debug.png")
                    print("After login screenshot saved")
                    
                    # Check current URL
                    current_url = page.url
                    print(f"Current URL after login: {current_url}")
                    
                    # Check if we're still on login page or moved elsewhere
                    if '/web/auth/login' not in current_url:
                        print("Successfully navigated away from login page!")
                    else:
                        print("Still on login page - login may have failed")
                else:
                    print("Submit button not found")
            else:
                print("Login or password input not found")
                
        except Exception as e:
            print(f"Error during test: {str(e)}")
            # Take screenshot on error
            try:
                await page.screenshot(path="error_debug.png")
            except:
                pass
        finally:
            print("Closing browser...")
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(simple_test())