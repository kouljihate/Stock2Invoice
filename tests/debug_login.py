import asyncio
from playwright.async_api import async_playwright

async def debug_login():
    """Debug the login page to find correct selectors"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto("http://127.0.0.1:5000/web/auth/login", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=20000)
            
            # Take a screenshot
            await page.screenshot(path="debug_login.png")
            
            # Get all input elements
            inputs = await page.query_selector_all("input")
            print(f"Found {len(inputs)} input elements")
            
            for i, input_elem in enumerate(inputs):
                input_type = await input_elem.get_attribute("type")
                input_name = await input_elem.get_attribute("name")
                input_id = await input_elem.get_attribute("id")
                placeholder = await input_elem.get_attribute("placeholder")
                print(f"Input {i}: type={input_type}, name={input_name}, id={input_id}, placeholder={placeholder}")
            
            # Try to find login field with various selectors
            login_selectors = [
                'input#login',
                'input[name="login"]',
                'input[type="email"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="login" i]',
                'input[placeholder*="Email" i]',
                'input[placeholder*="Login" i]'
            ]
            
            print("\nTrying login selectors:")
            for selector in login_selectors:
                elem = await page.query_selector(selector)
                if elem:
                    print(f"  Found with selector: {selector}")
                else:
                    print(f"  Not found with selector: {selector}")
            
            # Try to find password field
            password_selectors = [
                'input#password',
                'input[name="password"]',
                'input[type="password"]'
            ]
            
            print("\nTrying password selectors:")
            for selector in password_selectors:
                elem = await page.query_selector(selector)
                if elem:
                    print(f"  Found with selector: {selector}")
                else:
                    print(f"  Not found with selector: {selector}")
            
            # Try to find submit button
            submit_selectors = [
                'button[type="submit"]',
                '.btn-primary',
                'button:has-text("Log in")',
                'button:has-text("Sign In")'
            ]
            
            print("\nTrying submit selectors:")
            for selector in submit_selectors:
                elem = await page.query_selector(selector)
                if elem:
                    print(f"  Found with selector: {selector}")
                else:
                    print(f"  Not found with selector: {selector}")
                    
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_login())