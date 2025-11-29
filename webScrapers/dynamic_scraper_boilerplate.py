import asyncio
import requests
import json
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# ---------------------------
# Playwright Functions
# ---------------------------

async def run_playwright(url, headless=True, scroll_times=5, scroll_delay=1000):
    """
    Launch a browser, scroll to load content, capture network requests,
    and return HTML + potential API endpoints.
    """
    api_candidates = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()

        # Capture API/XHR responses
        page.on("response", lambda response: _capture_response(response, api_candidates))

        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(2)  # wait for extra JS content

        # Infinite scroll
        await infinite_scroll(page, scroll_times, scroll_delay)

        html = await page.content()
        await browser.close()
        return html, list(set(api_candidates))

def _capture_response(response, api_candidates):
    """Capture potential JSON API endpoints."""
    try:
        url = response.url
        if any(keyword in url for keyword in [".json", "api", "/data", "feed"]):
            api_candidates.append(url)
    except:
        pass

async def infinite_scroll(page, scrolls=5, delay=1000):
    """Scroll the page to load dynamic content."""
    print("[*] Attempting infinite scroll…")
    try:
        last_height = await page.evaluate("document.body.scrollHeight")
        for _ in range(scrolls):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(delay)
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        print("[+] Infinite scroll complete.")
    except Exception as e:
        print(f"[-] Infinite scroll failed: {e}")

# ---------------------------
# API Scraping
# ---------------------------

def try_api_scrape(api_candidates):
    """Attempt to scrape JSON APIs detected during browsing."""
    print("[*] Checking for JSON API endpoints…")
    for url in api_candidates:
        try:
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()
            print(f"[+] API endpoint found: {url}")
            return data
        except:
            continue
    print("[-] No usable API endpoints detected.")
    return None

# ---------------------------
# Main Scrape Function
# ---------------------------

async def scrape_dynamic(url, scroll_times=5, scroll_delay=1000):
    """
    Scrape a fully dynamic page using a headless browser.
    Returns:
    - Rendered HTML
    - Captured API JSON (if any)
    - List of potential API endpoints
    """
    html, api_candidates = await run_playwright(url, scroll_times=scroll_times, scroll_delay=scroll_delay)
    api_data = try_api_scrape(api_candidates)
    soup = BeautifulSoup(html, "html.parser")
    
    return {
        "html": str(soup),
        "api_data": api_data,
        "api_candidates": api_candidates
    }

# ---------------------------
# Runner
# ---------------------------

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    result = asyncio.run(scrape_dynamic(url))
    print(json.dumps(result, indent=2))
