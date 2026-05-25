"""Website enrichment worker — sync-thread version for Windows/Python 3.13 compat."""

import asyncio
import logging
import time
from typing import List, Optional, Callable
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from utils.parsers import extract_emails, extract_social_links, normalize_url

logger = logging.getLogger(__name__)

MAX_CONCURRENT = 4          # parallel threads
PAGE_TIMEOUT   = 15_000     # ms per page load
MAX_PAGES_PER_SITE = 3      # homepage + up to 2 sub-pages

_CONTACT_SLUGS = [
    "/contact", "/contact-us", "/contactus", "/get-in-touch",
    "/about", "/about-us", "/reach-us", "/enquiry",
]


# ── Sync enrichment (runs inside a thread) ───────────────────────────────────

def _sync_enrich_lead(website_url: str) -> dict:
    """Visit a website and extract emails + social links (sync Playwright)."""
    if not website_url:
        return _empty_enrichment()

    url = normalize_url(website_url)
    emails: List[str] = []
    social_links: dict = {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            ignore_https_errors=True,
        )
        page = context.new_page()

        # Block heavy media
        page.route(
            "**/*.{png,jpg,jpeg,gif,webp,svg,mp4,mp3,woff,woff2,ttf}",
            lambda r: r.abort()
        )

        pages_visited = 0
        urls_to_visit = [url]
        visited = set()

        while urls_to_visit and pages_visited < MAX_PAGES_PER_SITE:
            current_url = urls_to_visit.pop(0)
            if current_url in visited:
                continue
            visited.add(current_url)

            try:
                page.goto(current_url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
                time.sleep(1.5)

                html = page.content()
                page_emails = extract_emails(html)
                page_socials = extract_social_links(html)

                for e in page_emails:
                    if e not in emails:
                        emails.append(e)
                for platform, link in page_socials.items():
                    if platform not in social_links and link:
                        social_links[platform] = link

                pages_visited += 1

                # Queue contact/about pages from homepage only
                if pages_visited == 1:
                    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                    for slug in _CONTACT_SLUGS:
                        candidate = base + slug
                        if candidate not in visited:
                            urls_to_visit.append(candidate)
                            if len(urls_to_visit) >= 4:
                                break

            except PlaywrightTimeout:
                logger.warning(f"Timeout visiting {current_url}")
            except Exception as e:
                logger.warning(f"Error visiting {current_url}: {e}")

        context.close()
        browser.close()

    return {
        "emails": emails[:10],
        "social_links": social_links,
        "linkedin_url": social_links.get("linkedin"),
        "instagram_url": social_links.get("instagram"),
        "facebook_url": social_links.get("facebook"),
        "twitter_url": social_links.get("twitter"),
    }


# ── Async wrappers ──────────────────────────────────────────────────────────

async def enrich_lead(website_url: str) -> dict:
    """Async wrapper — runs sync enrichment in a thread."""
    return await asyncio.to_thread(_sync_enrich_lead, website_url)


async def enrich_leads_batch(
    leads: List[dict],
    on_progress: Optional[Callable[[dict], None]] = None,
) -> List[dict]:
    """
    Enrich a batch of leads concurrently (up to MAX_CONCURRENT at once).
    Each lead dict must have 'id' and 'website_url'.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    results = []

    async def _worker(lead: dict):
        async with semaphore:
            lead_id = lead["id"]
            website = lead.get("website_url", "")
            logger.info(f"Enriching lead {lead_id}: {website}")
            try:
                enrichment = await enrich_lead(website)
            except Exception as e:
                logger.error(f"Enrichment failed for {lead_id}: {e}")
                enrichment = _empty_enrichment()
            entry = {"lead_id": lead_id, "enrichment": enrichment}
            results.append(entry)
            if on_progress:
                on_progress(entry)
            return entry

    await asyncio.gather(*[_worker(lead) for lead in leads])
    return results


def _empty_enrichment() -> dict:
    return {
        "emails": [],
        "social_links": {},
        "linkedin_url": None,
        "instagram_url": None,
        "facebook_url": None,
        "twitter_url": None,
    }
