print("Testing imports...")
try:
    import playwright
    print("playwright imported")
except Exception as e:
    print(f"playwright import failed: {e}")

try:
    from playwright import sync_api
    print("playwright.sync_api imported")
except Exception as e:
    print(f"playwright.sync_api import failed: {e}")

try:
    from playwright.sync_api import expect, sync_playwright
    print("expect and sync_playwright imported")
except Exception as e:
    print(f"expect and sync_playwright import failed: {e}")

print("Done.")