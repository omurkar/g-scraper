"""Google Maps scraper — sync-thread version for Windows/Python 3.13 compatibility."""

import asyncio
import logging
import random
import re
import time
from typing import List, Optional, Callable
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


# ── Stealth helpers (sync versions) ──────────────────────────────────────────

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
]

STEALTH_JS = """
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
    window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){}, app: {} };
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(parameters)
    );
"""


def _human_sleep(min_s: float = 1.5, max_s: float = 3.5):
    time.sleep(random.uniform(min_s, max_s))


def _micro_sleep(min_ms: int = 200, max_ms: int = 800):
    time.sleep(random.randint(min_ms, max_ms) / 1000)


# ── Main async entry point ──────────────────────────────────────────────────

async def scrape_google_maps(
    keyword: str,
    location: str,
    max_results: int = 30,
    on_progress: Optional[Callable[[dict], None]] = None,
) -> List[dict]:
    """
    Scrape Google Maps for businesses matching keyword + location.
    Runs Playwright's SYNC API in a separate thread to avoid
    Windows/Python 3.13 event-loop incompatibility.
    """
    return await asyncio.to_thread(
        _sync_scrape, keyword, location, max_results, on_progress
    )


# ── Sync scraper (runs inside a thread) ─────────────────────────────────────

def _sync_scrape(
    keyword: str,
    location: str,
    max_results: int,
    on_progress: Optional[Callable],
) -> List[dict]:
    """Synchronous scraper — safe to call from asyncio.to_thread()."""
    results: List[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1366,768",
                "--lang=en-US,en",
                "--disable-extensions",
                "--disable-infobars",
                "--disable-popup-blocking",
            ],
        )

        vp = random.choice(VIEWPORTS)
        context = browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport=vp,
            locale="en-US",
            timezone_id="America/New_York",
            ignore_https_errors=True,
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            },
        )
        page = context.new_page()
        page.add_init_script(STEALTH_JS)

        # Block heavy resources
        page.route(
            "**/*.{png,jpg,jpeg,gif,mp4,mp3,woff,woff2,ttf,ico}",
            lambda r: r.abort()
        )

        try:
            # ── Step 1: Navigate to Google Maps ──────────────────────────
            query = f"{keyword} in {location}"
            logger.info(f"Opening Google Maps…")
            page.goto("https://www.google.com/maps", wait_until="domcontentloaded", timeout=20_000)
            _human_sleep(2.0, 3.5)

            # Dismiss consent
            _dismiss_consent_sync(page)

            # ── Step 2: Type the search query ────────────────────────────
            logger.info(f"Searching for: {query}")

            search_input = _find_search_input(page)
            if search_input is None:
                logger.warning("Search input not found — using direct URL")
                return _direct_url_scrape_sync(page, keyword, location, max_results, on_progress)

            search_input.click()
            _micro_sleep(300, 600)
            search_input.fill("")
            _micro_sleep(200, 400)

            # Type character-by-character for stealth
            for char in query:
                page.keyboard.type(char, delay=random.randint(40, 120))
            _micro_sleep(400, 800)
            page.keyboard.press("Enter")

            # ── Step 3: Wait for results feed ────────────────────────────
            _human_sleep(3.0, 5.0)
            feed = _wait_for_feed_sync(page)
            if not feed:
                logger.warning("Feed not found — falling back to direct URL")
                return _direct_url_scrape_sync(page, keyword, location, max_results, on_progress)

            # ── Step 4: Scroll to load results ───────────────────────────
            biz_links = _scroll_and_collect_sync(page, feed, max_results)
            logger.info(f"Collected {len(biz_links)} place links")

            # ── Step 5: Extract details from each place ──────────────────
            for i, link in enumerate(biz_links[:max_results]):
                if len(results) >= max_results:
                    break
                try:
                    biz = _extract_place_sync(page, link)
                    if biz and biz.get("business_name"):
                        results.append(biz)
                        logger.info(f"  [{len(results)}/{max_results}] {biz['business_name']}")
                        if on_progress:
                            on_progress({"lead": biz, "count": len(results)})
                    _micro_sleep(600, 1400)
                except Exception as e:
                    logger.warning(f"  Place {i} error: {e}")

        except Exception as e:
            logger.error(f"Scraper fatal: {e}", exc_info=True)
        finally:
            context.close()
            browser.close()

    logger.info(f"Scraping done: {len(results)} leads")
    return results


# ── Helpers ──────────────────────────────────────────────────────────────────

def _find_search_input(page):
    """Locate the Google Maps search box."""
    for sel in [
        'input#searchboxinput',
        'input[name="q"]',
        'input[placeholder*="Search"]',
        'input[aria-label*="Search"]',
    ]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=5000):
                return el
        except Exception:
            continue
    return None


def _dismiss_consent_sync(page):
    """Click through consent/cookie banners."""
    for selector in [
        'button:has-text("Accept all")',
        'button:has-text("Accept")',
        'button:has-text("Agree")',
        'button:has-text("I agree")',
        'button[aria-label*="Accept"]',
        'form[action*="consent"] button',
        '#L2AGLb',
    ]:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=2500):
                btn.click()
                logger.info(f"Dismissed consent via: {selector}")
                _micro_sleep(800, 1500)
                return
        except Exception:
            pass


def _wait_for_feed_sync(page, timeout: int = 15_000):
    """Wait for the Google Maps results feed."""
    for sel in [
        'div[role="feed"]',
        'div.m6QErb[role="region"]',
        'div.m6QErb',
        '[aria-label*="Results for"]',
        '[aria-label*="results"]',
    ]:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            logger.info(f"Feed found: {sel}")
            return loc
        except PlaywrightTimeout:
            continue
    return None


def _scroll_and_collect_sync(page, feed, max_results: int) -> List[str]:
    """Scroll the feed and collect /maps/place/ links."""
    target = max_results + 10
    scroll_attempts = 0
    max_scrolls = 20
    last_count = 0
    stale_rounds = 0

    while scroll_attempts < max_scrolls:
        links = page.evaluate("""() => {
            const anchors = document.querySelectorAll('a[href*="/maps/place/"]');
            const seen = new Set();
            const result = [];
            for (const a of anchors) {
                const h = a.href.split('?')[0];
                if (!seen.has(h)) { seen.add(h); result.push(a.href); }
            }
            return result;
        }""")

        current_count = len(links)
        logger.info(f"  Scroll {scroll_attempts}: {current_count} links")

        if current_count >= target:
            break

        if current_count == last_count:
            stale_rounds += 1
            if stale_rounds >= 3:
                logger.info("No new links after 3 scrolls — stopping")
                break
        else:
            stale_rounds = 0
        last_count = current_count

        page.evaluate("""() => {
            const feed = document.querySelector('div[role="feed"]') ||
                         document.querySelector('.m6QErb');
            if (feed) feed.scrollBy(0, 800);
        }""")
        _human_sleep(1.8, 3.2)

        end_markers = page.locator(
            'span:has-text("reached the end"), '
            'span:has-text("You\'ve reached the end"), '
            'p:has-text("reached the end")'
        ).count()
        if end_markers > 0:
            logger.info("End of results list reached")
            break

        scroll_attempts += 1

    # Final collection
    final = page.evaluate("""() => {
        const anchors = document.querySelectorAll('a[href*="/maps/place/"]');
        const seen = new Set();
        const result = [];
        for (const a of anchors) {
            const h = a.href.split('?')[0];
            if (!seen.has(h)) { seen.add(h); result.push(a.href); }
        }
        return result;
    }""")
    return final[:max_results + 5]


def _extract_place_sync(page, maps_url: str) -> Optional[dict]:
    """Navigate to a Maps place page and extract details."""
    try:
        page.goto(maps_url, wait_until="domcontentloaded", timeout=15_000)
        _human_sleep(1.2, 2.5)
    except PlaywrightTimeout:
        logger.warning(f"Timeout loading {maps_url}")
        return None
    except Exception as e:
        logger.warning(f"Error loading {maps_url}: {e}")
        return None

    data = page.evaluate("""() => {
        const result = {};

        // Business name
        const h1 = document.querySelector('h1.DUwDvf') ||
                   document.querySelector('h1[class*="fontHeadlineLarge"]') ||
                   document.querySelector('h1');
        result.name = h1 ? h1.innerText.trim() : '';

        // Rating
        const ratingEl = document.querySelector('div.F7nice span[aria-hidden="true"]') ||
                        document.querySelector('.fontDisplayLarge');
        result.rating = ratingEl ? ratingEl.innerText.trim() : '';

        // Review count
        const reviewEl = document.querySelector('div.F7nice span[aria-label*="review"]') ||
                        document.querySelector('span[aria-label*="reviews"]');
        result.reviews = reviewEl ? reviewEl.getAttribute('aria-label') : '';

        // Category
        const catEl = document.querySelector('button.DkEaL') ||
                     document.querySelector('span.DkEaL') ||
                     document.querySelector('[jsaction*="category"]');
        result.category = catEl ? catEl.innerText.trim() : '';

        // Address
        const addrBtn = document.querySelector('button[data-item-id="address"]') ||
                       document.querySelector('[data-tooltip="Copy address"]');
        result.address = addrBtn ? addrBtn.innerText.trim() : '';

        // Phone
        const phoneBtn = [...document.querySelectorAll('button[data-item-id]')]
            .find(b => b.getAttribute('data-item-id').startsWith('phone:'));
        result.phone = phoneBtn ? phoneBtn.innerText.trim() : '';

        // Website
        const websiteLink = document.querySelector('a[data-item-id="authority"]');
        result.website = websiteLink ? websiteLink.href : '';

        // Alternate phone
        if (!result.phone) {
            const allBtns = document.querySelectorAll('button[data-tooltip]');
            for (const b of allBtns) {
                const tip = b.getAttribute('data-tooltip') || '';
                if (tip.toLowerCase().includes('phone') || tip.toLowerCase().includes('copy phone')) {
                    result.phone = b.innerText.trim();
                    break;
                }
            }
        }

        return result;
    }""")

    if not data:
        return None

    # Parse rating
    rating = None
    try:
        rating = float(data.get("rating", "").replace(",", ".")) if data.get("rating") else None
    except (ValueError, AttributeError):
        pass

    # Parse review count
    review_count = None
    review_text = data.get("reviews", "")
    if review_text:
        m = re.search(r'[\d,]+', review_text)
        if m:
            try:
                review_count = int(m.group(0).replace(',', ''))
            except ValueError:
                pass

    name = data.get("name", "").strip()
    if not name:
        m2 = re.search(r'/maps/place/([^/@]+)', maps_url)
        if m2:
            name = m2.group(1).replace('+', ' ').replace('%20', ' ').replace('%26', '&')

    return {
        "business_name": name or None,
        "rating": rating,
        "review_count": review_count,
        "category": data.get("category") or None,
        "address": data.get("address") or None,
        "phone": data.get("phone") or None,
        "website_url": data.get("website") or None,
        "google_maps_url": page.url,
    }


def _direct_url_scrape_sync(page, keyword, location, max_results, on_progress) -> List[dict]:
    """Fallback: navigate directly to /maps/search/ URL."""
    query = f"{keyword} in {location}"
    url = f"https://www.google.com/maps/search/{quote_plus(query)}"
    results = []

    page.goto(url, wait_until="networkidle", timeout=25_000)
    _human_sleep(2.5, 4.0)
    _dismiss_consent_sync(page)

    feed = _wait_for_feed_sync(page)
    if not feed:
        logger.error("Feed not found in direct URL mode either")
        return results

    biz_links = _scroll_and_collect_sync(page, feed, max_results)
    logger.info(f"Direct mode: {len(biz_links)} links")

    for i, link in enumerate(biz_links[:max_results]):
        if len(results) >= max_results:
            break
        try:
            biz = _extract_place_sync(page, link)
            if biz and biz.get("business_name"):
                results.append(biz)
                if on_progress:
                    on_progress({"lead": biz, "count": len(results)})
            _micro_sleep(600, 1400)
        except Exception as e:
            logger.warning(f"  Place {i} error: {e}")

    return results
