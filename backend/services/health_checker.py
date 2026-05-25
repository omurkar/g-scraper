"""
Website Health Checker — audits a lead's website for:
- Existence (any HTTP response)
- SSL/HTTPS
- Load time (< 4 seconds = fast)
- Mobile responsiveness (viewport meta tag present)

Tags each lead as:
  NO_SITE      — No website URL found
  FIX_NEEDED   — Site exists but has issues (no HTTPS, slow, not mobile-ready)
  GOOD_SITE    — Healthy: HTTPS + fast + mobile-friendly
"""

import asyncio
import logging
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 8
SLOW_THRESHOLD_MS = 4000   # > 4s = poor


class HealthResult:
    def __init__(
        self,
        tag: str,                          # NO_SITE | FIX_NEEDED | GOOD_SITE
        ssl_ok: bool = False,
        load_time_ms: int = 0,
        mobile_friendly: bool = False,
        status_code: Optional[int] = None,
        issues: Optional[list] = None,
    ):
        self.tag = tag
        self.ssl_ok = ssl_ok
        self.load_time_ms = load_time_ms
        self.mobile_friendly = mobile_friendly
        self.status_code = status_code
        self.issues = issues or []

    def to_dict(self) -> dict:
        return {
            "website_tag": self.tag,
            "ssl_ok": self.ssl_ok,
            "load_time_ms": self.load_time_ms,
            "mobile_friendly": self.mobile_friendly,
            "http_status": self.status_code,
            "health_issues": self.issues,
        }


async def audit_website(website_url: Optional[str]) -> HealthResult:
    """Run a full health audit on a website URL."""
    if not website_url or not website_url.strip():
        return HealthResult(tag="NO_SITE")

    url = website_url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")

    issues = []

    # ── 1. SSL check ──────────────────────────────────────────────────────────
    ssl_ok = url.startswith("https://")
    if not ssl_ok:
        issues.append("No HTTPS")

    # ── 2. Fetch + load time ──────────────────────────────────────────────────
    start = time.monotonic()
    html_content = ""
    status_code = None

    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                              "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            },
            verify=False,   # Skip cert errors — just checking reachability
        ) as client:
            resp = await client.get(url)
            status_code = resp.status_code
            html_content = resp.text[:50_000]   # First 50KB is enough

            elapsed_ms = int((time.monotonic() - start) * 1000)

    except httpx.TimeoutException:
        elapsed_ms = int(TIMEOUT_SECONDS * 1000)
        issues.append(f"Timeout (>{TIMEOUT_SECONDS}s)")
        return HealthResult(
            tag="FIX_NEEDED",
            ssl_ok=ssl_ok,
            load_time_ms=elapsed_ms,
            mobile_friendly=False,
            status_code=None,
            issues=issues,
        )
    except Exception as e:
        issues.append(f"Unreachable ({type(e).__name__})")
        return HealthResult(
            tag="FIX_NEEDED",
            ssl_ok=ssl_ok,
            load_time_ms=0,
            mobile_friendly=False,
            status_code=None,
            issues=issues,
        )

    # ── 3. Load time check ────────────────────────────────────────────────────
    load_time_ms = elapsed_ms
    if load_time_ms > SLOW_THRESHOLD_MS:
        issues.append(f"Slow load ({load_time_ms}ms > {SLOW_THRESHOLD_MS}ms)")

    if status_code and status_code >= 400:
        issues.append(f"HTTP {status_code} error")

    # ── 4. Mobile responsiveness ──────────────────────────────────────────────
    mobile_friendly = _check_mobile_friendly(html_content)
    if not mobile_friendly:
        issues.append("Not mobile-friendly (no viewport meta)")

    # ── 5. Final tag ──────────────────────────────────────────────────────────
    if not issues:
        tag = "GOOD_SITE"
    else:
        tag = "FIX_NEEDED"

    return HealthResult(
        tag=tag,
        ssl_ok=ssl_ok,
        load_time_ms=load_time_ms,
        mobile_friendly=mobile_friendly,
        status_code=status_code,
        issues=issues,
    )


def _check_mobile_friendly(html: str) -> bool:
    """Check if the page has a viewport meta tag (basic mobile signal)."""
    lower = html.lower()
    return (
        'name="viewport"' in lower
        or "name='viewport'" in lower
        or "viewport" in lower[:2000]   # Usually in <head>
    )


async def audit_leads_batch(leads: list, max_concurrent: int = 8) -> dict:
    """
    Audit a list of leads concurrently.
    Returns dict: {lead_id: HealthResult.to_dict()}
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {}

    async def _check(lead):
        async with semaphore:
            lead_id = lead["id"]
            url = lead.get("website_url")
            try:
                result = await audit_website(url)
                results[lead_id] = result.to_dict()
                logger.info(f"  Health [{result.tag}] {url or '—'}")
            except Exception as e:
                logger.warning(f"  Health check error for {lead_id}: {e}")
                results[lead_id] = HealthResult(tag="NO_SITE").to_dict()

    await asyncio.gather(*[_check(l) for l in leads])
    return results
