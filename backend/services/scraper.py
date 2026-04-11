"""Google Maps scraper — robust version with full stealth & interaction simulation."""

import asyncio
import logging
import random
import re
from typing import List, Optional, Callable
from urllib.parse import quote_plus

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from utils.stealth import apply_stealth_scripts, get_stealth_context_options, human_delay, micro_delay

logger = logging.getLogger(__name__)


async def scrape_google_maps(
    keyword: str,
    location: str,
    max_results: int = 30,
    on_progress: Optional[Callable[[dict], None]] = None,
) -> List[dict]:
    """
    Scrape Google Maps for businesses matching keyword + location.
    Strategy: Navigate to Maps, search, scroll feed, collect place links, then extract details.
    """
    results: List[dict] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
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

        ctx_opts = await get_stealth_context_options()
        context = await browser.new_context(**ctx_opts)
        page = await context.new_page()
        await apply_stealth_scripts(page)

        # Block irrelevant resources to speed things up
        await page.route(
            "**/*.{png,jpg,jpeg,gif,mp4,mp3,woff,woff2,ttf,ico}",
            lambda r: r.abort()
        )

        try:
            # ── Step 1: Go to google.com/maps first (more natural) ──────────
            logger.info("Opening Google Maps…")
            await page.goto("https://www.google.com/maps", wait_until="domcontentloaded", timeout=20_000)
            await human_delay(2.0, 3.5)

            # Dismiss consent/cookie banners
            await _dismiss_consent(page)

            # ── Step 2: Type query into the search box ──────────────────────
            query = f"{keyword} in {location}"
            logger.info(f"Searching for: {query}")

            search_selectors = [
                'input#searchboxinput',
                'input[name="q"]',
                'input[placeholder*="Search"]',
                'input[aria-label*="Search"]',
            ]
            search_input = None
            for sel in search_selectors:
                try:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=5000):
                        search_input = el
                        break
                except Exception:
                    continue

            if search_input is None:
                logger.error("Search input not found — using direct URL approach")
                return await _direct_url_scrape(page, keyword, location, max_results, on_progress)

            # Human-like typing
            await search_input.click()
            await micro_delay(300, 600)
            await search_input.fill("")
            await micro_delay(200, 400)
            for char in query:
                await page.keyboard.type(char, delay=random.randint(40, 120))
            await micro_delay(400, 800)
            await page.keyboard.press("Enter")

            # ── Step 3: Wait for results feed ───────────────────────────────
            await human_delay(3.0, 5.0)

            feed = await _wait_for_feed(page)
            if not feed:
                logger.warning("Feed not found after typing — falling back to direct URL")
                return await _direct_url_scrape(page, keyword, location, max_results, on_progress)

            # ── Step 4: Scroll to load more results ─────────────────────────
            biz_links = await _scroll_and_collect_links(page, feed, max_results)
            logger.info(f"Collected {len(biz_links)} place links")

            # ── Step 5: Extract details from each place page ─────────────────
            for i, link in enumerate(biz_links[:max_results]):
                if len(results) >= max_results:
                    break
                try:
                    biz = await _extract_place_details(page, link)
                    if biz and biz.get("business_name"):
                        results.append(biz)
                        logger.info(f"  [{len(results)}/{max_results}] {biz['business_name']}")
                        if on_progress:
                            on_progress({"lead": biz, "count": len(results)})
                    await micro_delay(600, 1400)
                except Exception as e:
                    logger.warning(f"  Place {i} error: {e}")

        except Exception as e:
            logger.error(f"Scraper fatal: {e}", exc_info=True)
        finally:
            await context.close()
            await browser.close()

    logger.info(f"Scraping done: {len(results)} leads")
    return results


async def _direct_url_scrape(page, keyword, location, max_results, on_progress) -> List[dict]:
    """Fallback: navigate directly to /maps/search/ URL."""
    query = f"{keyword} in {location}"
    url = f"https://www.google.com/maps/search/{quote_plus(query)}"
    results = []

    await page.goto(url, wait_until="networkidle", timeout=25_000)
    await human_delay(2.5, 4.0)
    await _dismiss_consent(page)

    feed = await _wait_for_feed(page)
    if not feed:
        logger.error("Feed not found in direct URL mode either")
        return results

    biz_links = await _scroll_and_collect_links(page, feed, max_results)
    logger.info(f"Direct mode: {len(biz_links)} links")

    for i, link in enumerate(biz_links[:max_results]):
        if len(results) >= max_results:
            break
        try:
            biz = await _extract_place_details(page, link)
            if biz and biz.get("business_name"):
                results.append(biz)
                if on_progress:
                    on_progress({"lead": biz, "count": len(results)})
            await micro_delay(600, 1400)
        except Exception as e:
            logger.warning(f"  Place {i} error: {e}")

    return results


async def _dismiss_consent(page) -> None:
    """Try to click through any consent/cookie banners."""
    for selector in [
        'button:has-text("Accept all")',
        'button:has-text("Accept")',
        'button:has-text("Agree")',
        'button:has-text("I agree")',
        'button[aria-label*="Accept"]',
        'form[action*="consent"] button',
        '#L2AGLb',   # Google's "Accept all" button ID
    ]:
        try:
            btn = page.locator(selector).first
            if await btn.is_visible(timeout=2500):
                await btn.click()
                logger.info(f"Dismissed consent via: {selector}")
                await micro_delay(800, 1500)
                return
        except Exception:
            pass


async def _wait_for_feed(page, timeout: int = 15_000):
    """Wait for the Google Maps results feed to appear."""
    selectors = [
        'div[role="feed"]',
        'div.m6QErb[role="region"]',
        'div.m6QErb',
        '[aria-label*="Results for"]',
        '[aria-label*="results"]',
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            await loc.wait_for(state="visible", timeout=timeout)
            logger.info(f"Feed found: {sel}")
            return loc
        except PlaywrightTimeout:
            continue
    return None


async def _scroll_and_collect_links(page, feed, max_results: int) -> List[str]:
    """Scroll the results feed and collect all /maps/place/ links."""
    target_count = max_results + 10
    scroll_attempts = 0
    max_scrolls = 20
    last_count = 0
    stale_rounds = 0

    while scroll_attempts < max_scrolls:
        # Collect current place links
        links = await page.evaluate("""() => {
            const anchors = document.querySelectorAll('a[href*="/maps/place/"]');
            const seen = new Set();
            const result = [];
            for (const a of anchors) {
                const h = a.href.split('?')[0];  // normalize URL
                if (!seen.has(h)) { seen.add(h); result.push(a.href); }
            }
            return result;
        }""")

        current_count = len(links)
        logger.info(f"  Scroll {scroll_attempts}: {current_count} links")

        if current_count >= target_count:
            break

        # Check if we've stalled
        if current_count == last_count:
            stale_rounds += 1
            if stale_rounds >= 3:
                logger.info("No new links after 3 scroll rounds — stopping")
                break
        else:
            stale_rounds = 0
        last_count = current_count

        # Scroll the feed
        await page.evaluate("""() => {
            const feed = document.querySelector('div[role="feed"]') ||
                         document.querySelector('.m6QErb');
            if (feed) {
                feed.scrollBy(0, 800);
            }
        }""")
        await human_delay(1.8, 3.2)

        # Check end-of-list marker
        end_markers = await page.locator(
            'span:has-text("reached the end"), '
            'span:has-text("You\'ve reached the end"), '
            'p:has-text("reached the end")'
        ).count()
        if end_markers > 0:
            logger.info("End of results list reached")
            break

        scroll_attempts += 1

    # Final collection
    final_links = await page.evaluate("""() => {
        const anchors = document.querySelectorAll('a[href*="/maps/place/"]');
        const seen = new Set();
        const result = [];
        for (const a of anchors) {
            const h = a.href.split('?')[0];
            if (!seen.has(h)) { seen.add(h); result.push(a.href); }
        }
        return result;
    }""")
    return final_links[:max_results + 5]


async def _extract_place_details(page, maps_url: str) -> Optional[dict]:
    """Navigate to a Maps business page and extract all available details."""
    try:
        await page.goto(maps_url, wait_until="domcontentloaded", timeout=15_000)
        await human_delay(1.2, 2.5)
    except PlaywrightTimeout:
        logger.warning(f"Timeout loading {maps_url}")
        return None
    except Exception as e:
        logger.warning(f"Error loading {maps_url}: {e}")
        return None

    # Extract all data via a single JS evaluation for speed
    data = await page.evaluate("""() => {
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

        // Try alternate phone pattern
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
    rating: Optional[float] = None
    try:
        rating = float(data.get("rating", "").replace(",", ".")) if data.get("rating") else None
    except (ValueError, AttributeError):
        pass

    # Parse review count
    review_count: Optional[int] = None
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
        # Fallback: extract from URL
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
