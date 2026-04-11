"""Email and social-media link extraction utilities."""

import re
from typing import List, Dict, Optional
from urllib.parse import urlparse

# ─── Email Regex ──────────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

# Domains that are clearly not real business emails
_THROWAWAY_DOMAINS = {
    "example.com", "test.com", "sentry.io", "wixpress.com",
    "squarespace.com", "shopify.com", "amazonaws.com",
    "cloudflare.com", "googletagmanager.com", "schema.org",
}


def extract_emails(text: str) -> List[str]:
    """Extract unique, valid-looking email addresses from a block of text."""
    found = _EMAIL_RE.findall(text)
    seen = set()
    result = []
    for email in found:
        email = email.lower().strip(".,;")
        domain = email.split("@")[-1]
        if domain in _THROWAWAY_DOMAINS:
            continue
        if email not in seen:
            seen.add(email)
            result.append(email)
    return result


# ─── Social Link Patterns ─────────────────────────────────────────────────────
_SOCIAL_PATTERNS: Dict[str, re.Pattern] = {
    "linkedin": re.compile(
        r"https?://(www\.)?linkedin\.com/(company|in|pub)/[^\s\"'<>]+",
        re.IGNORECASE,
    ),
    "instagram": re.compile(
        r"https?://(www\.)?instagram\.com/[^\s\"'<>?/]+/?",
        re.IGNORECASE,
    ),
    "facebook": re.compile(
        r"https?://(www\.)?facebook\.com/[^\s\"'<>?]+",
        re.IGNORECASE,
    ),
    "twitter": re.compile(
        r"https?://(www\.)?(twitter|x)\.com/[^\s\"'<>?/]+/?",
        re.IGNORECASE,
    ),
    "youtube": re.compile(
        r"https?://(www\.)?youtube\.com/(channel|user|c)/[^\s\"'<>?]+",
        re.IGNORECASE,
    ),
}


def extract_social_links(html: str) -> Dict[str, Optional[str]]:
    """Scan HTML for social media profile links. Returns first match per platform."""
    result: Dict[str, Optional[str]] = {}
    for platform, pattern in _SOCIAL_PATTERNS.items():
        matches = pattern.findall(html)
        if matches:
            # pattern.findall returns tuple groups — re-search for full match
            m = pattern.search(html)
            if m:
                result[platform] = m.group(0).rstrip("/")
    return result


def is_contact_page(url: str) -> bool:
    """Heuristic: does this URL look like a contact/about page?"""
    path = urlparse(url).path.lower()
    keywords = ["contact", "about", "reach", "connect", "touch", "get-in-touch", "enquiry"]
    return any(k in path for k in keywords)


def normalize_url(url: str) -> str:
    """Ensure URL has scheme."""
    if not url:
        return url
    if not url.startswith(("http://", "https://")):
        return "https://" + url.lstrip("/")
    return url
