"""Anti-detection utilities for Playwright — stealth, delays, user-agents."""

import random
import asyncio
from typing import Optional
from playwright.async_api import BrowserContext, Page

# ─── User-Agent Pool ──────────────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/116.0.0.0",
]

# ─── Viewport Pool ────────────────────────────────────────────────────────────
VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1280, "height": 800},
    {"width": 2560, "height": 1440},
]


def random_ua() -> str:
    """Pick a random user-agent string."""
    return random.choice(USER_AGENTS)


def random_viewport() -> dict:
    """Pick a random desktop viewport."""
    return random.choice(VIEWPORTS)


async def human_delay(min_s: float = 1.5, max_s: float = 4.0) -> None:
    """Sleep for a random human-like duration."""
    await asyncio.sleep(random.uniform(min_s, max_s))


async def micro_delay(min_ms: int = 200, max_ms: int = 800) -> None:
    """Very short pause — simulate reading/thinking."""
    await asyncio.sleep(random.randint(min_ms, max_ms) / 1000)


async def apply_stealth_scripts(page: Page) -> None:
    """Inject JS patches to mask Playwright/headless indicators."""
    await page.add_init_script("""
        // Mask webdriver flag
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });

        // Override plugins to look like a real browser
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });

        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });

        // Fix chrome object
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {},
        };

        // Patch permissions API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );

        // Randomize canvas fingerprint slightly
        const toBlob = HTMLCanvasElement.prototype.toBlob;
        const toDataURL = HTMLCanvasElement.prototype.toDataURL;
        const getImageData = CanvasRenderingContext2D.prototype.getImageData;

        const noise = () => Math.random() * 0.01;

        CanvasRenderingContext2D.prototype.getImageData = function(x, y, w, h) {
            const data = getImageData.apply(this, arguments);
            for (let i = 0; i < data.data.length; i += 4) {
                data.data[i] = Math.min(255, data.data[i] + Math.floor(noise() * 10));
            }
            return data;
        };
    """)


async def get_stealth_context_options() -> dict:
    """Return browser context options that minimise detection."""
    vp = random_viewport()
    return {
        "user_agent": random_ua(),
        "viewport": vp,
        "locale": "en-US",
        "timezone_id": "America/New_York",
        "geolocation": None,
        "permissions": [],
        "java_script_enabled": True,
        "ignore_https_errors": True,
        "extra_http_headers": {
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        },
    }
