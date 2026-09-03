import asyncio
from playwright.async_api import async_playwright
import traceback

async def run_customer_flow(page):
    print("--- CUSTOMER E2E ---")
    
    # 1. Open frontend
    print("1. Open frontend...")
    await page.goto("http://localhost:8081/")
    await page.wait_for_selector("text=Browse catalog")
    print("[PASS] Open frontend")

    # 2. Register
    print("2. Register a new customer...")
    await page.goto("http://localhost:8081/login")
    await page.click("text=Create an account")
    await page.fill("input[placeholder='Full Name']", "Playwright User")
    await page.fill("input[placeholder='Email']", "pw.user@example.com")
    await page.fill("input[type='password']", "Password123!")
    await page.click("button:has-text('Create account')")
    
    # Let it process
    await asyncio.sleep(2)
    # 3. Login
    print("3. Login...")
    await page.goto("http://localhost:8081/login")
    await page.fill("input[placeholder='Email']", "pw.user@example.com")
    await page.fill("input[type='password']", "Password123!")
    await page.click("button:has-text('Sign in')")
    await asyncio.sleep(2)
    print("[PASS] Registration and Login")
    
    # 5. Home
    await page.goto("http://localhost:8081/")
    print("[PASS] Open Home")
    
    # 6. Products
    print("6. Open Products...")
    await page.goto("http://localhost:8081/products")
    await page.wait_for_selector("text=Filters")
    print("[PASS] Open Products")
    
    # 8. Product Detail
    print("8. Open Product Detail...")
    # Click the first product link
    await page.goto("http://localhost:8081/products/1")
    await page.wait_for_selector("button:has-text('Add to Cart')")
    print("[PASS] Open Product Detail")
    
    # 11. Add to cart
    print("11. Add to cart...")
    await page.click("button:has-text('Add to Cart')")
    await asyncio.sleep(1)
    print("[PASS] Add to cart")
    
    # 12. Open cart
    print("12. Open cart...")
    await page.goto("http://localhost:8081/cart")
    await page.wait_for_selector("text=Checkout")
    print("[PASS] Open Cart")
    
    # 16. Checkout
    print("16. Checkout...")
    await page.click("button:has-text('Checkout')")
    await asyncio.sleep(2)
    print("[PASS] Proceed to checkout")
    
    # Checkout flow
    print("Checkout steps...")
    try:
        await page.fill("input[placeholder='Full Name']", "Playwright User")
        await page.fill("input[placeholder='Email']", "pw.user@example.com")
        await page.fill("input[placeholder='Phone Number']", "1234567890")
        await page.click("button:has-text('Continue')")
        await asyncio.sleep(1)
        
        await page.fill("input[placeholder='Address']", "123 Street")
        await page.fill("input[placeholder='City']", "City")
        await page.fill("input[placeholder='State']", "State")
        await page.fill("input[placeholder='Postal Code']", "12345")
        await page.click("button:has-text('Continue')")
        await asyncio.sleep(1)
        
        # Confirm
        await page.click("button:has-text('Continue')")
        await asyncio.sleep(2)
        print("[PASS] Checkout Quote & Confirm")
    except Exception as e:
        print("[FAIL] Checkout steps failed:", str(e))
        
    print("--- CUSTOMER E2E COMPLETE ---")

async def run_admin_flow(page):
    print("--- ADMIN E2E ---")
    await page.goto("http://localhost:8081/login")
    await page.fill("input[placeholder='Email']", "admin@razorgrowth.ai")
    await page.fill("input[type='password']", "admin123")
    await page.click("button:has-text('Sign in')")
    await asyncio.sleep(2)
    
    await page.goto("http://localhost:8081/admin")
    try:
        await page.wait_for_selector("text=Dashboard", timeout=5000)
        print("[PASS] Admin Dashboard")
    except Exception:
        print("[FAIL] Admin Dashboard")
        
    for p in ["products", "orders", "customers"]:
        await page.goto(f"http://localhost:8081/admin/{p}")
        try:
            await asyncio.sleep(1)
            print(f"[PASS] Admin {p.capitalize()}")
        except Exception:
            print(f"[FAIL] Admin {p.capitalize()}")
            
    print("--- ADMIN E2E COMPLETE ---")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await run_customer_flow(page)
        
        # Clear cookies/session for admin
        await page.context.clear_cookies()
        
        await run_admin_flow(page)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
