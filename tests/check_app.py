import urllib.request
import urllib.error
import sys

def check_application_available():
    """Check if the application is running and accessible"""
    BASE_URL = "http://127.0.0.1:5000"
    try:
        response = urllib.request.urlopen(f"{BASE_URL}/web/auth/login", timeout=5)
        print(f"Application is running! Status: {response.getcode()}")
        return True
    except Exception as e:
        print(f"Error: Application is not running at {BASE_URL}. Please start the application first.")
        print(f"Details: {str(e)}")
        return False

if __name__ == "__main__":
    if check_application_available():
        sys.exit(0)
    else:
        sys.exit(1)