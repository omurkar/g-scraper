"""Website enrichment worker — visits each lead's site to extract emails & socials."""

import asyncio
import logging
from typing import List, Optional, Callable
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from utils.stealth import apply_stealth_scripts, get_stealth_context_options, human_delay
from utils.parsers import extract_emails, extract_social_links, normalize_url

logger = logging.getLogger(__name__)

MAX_CONCURRENT = 4          # parallel browser contexts
PAGE_TIMEOUT   = 15_000     # ms per page load
MAX_PAGES_PER_SITE = 3      # homepage + up to 2 sub-pages (/contact, /about)

_CONTACT_SLUGS = [
    "/contact", "/contact-us", "/contactus", "/get-in-touch",
    "/about", "/about-us", "/reach-us", "/enquiry",
]


async def enrich_lead(website_url: str) -> dict:
    """
    Visit a business website and extract emails + social links.
    Returns enrichment dict: {emails, social_links, linkedin_url, ...}
    """
    if not website_url:
        return _empty_enrichment()

    url = normalize_url(website_url)
    emails: List[str] = []
    social_links: dict = {}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        ctx_opts = await get_stealth_context_options()
        context = await browser.new_context(**ctx_opts)
        page = await context.new_page()
        await apply_stealth_scripts(page)

        # Block heavy media to speed things up
        await page.route(
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
                await page.goto(current_url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
                await asyncio.sleep(1.5)

                html = await page.content()
                page_emails = extract_emails(html)
                page_socials = extract_social_links(html)

                # Merge results
                for e in page_emails:
                    if e not in emails:
                        emails.append(e)
                for platform, link in page_socials.items():
                    if platform not in social_links and link:
                        social_links[platform] = link

                pages_visited += 1

                # Queue contact/about pages from the homepage only
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

        await context.close()
        await browser.close()

    return {
        "emails": emails[:10],   # cap at 10
        "social_links": social_links,
        "linkedin_url": social_links.get("linkedin"),
        "instagram_url": social_links.get("instagram"),
        "facebook_url": social_links.get("facebook"),
        "twitter_url": social_links.get("twitter"),
    }


async def enrich_leads_batch(
    leads: List[dict],
    on_progress: Optional[Callable[[dict], None]] = None,
) -> List[dict]:
    """
    Enrich a batch of leads concurrently (up to MAX_CONCURRENT at once).
    Each lead dict must have 'id' and 'website_url'.
    Returns list of {lead_id, enrichment} dicts.
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
