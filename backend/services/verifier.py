"""Gemini AI-powered email verification and lead quality scoring."""

import json
import logging
import re
from typing import Optional

import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)

_MODEL_NAME = "gemini-2.0-flash"

_SYSTEM_PROMPT = """You are an expert B2B lead quality analyst. Your job is to assess whether an extracted email address belongs to the listed business, and to score the overall lead quality.

You will be given:
- Business name and category
- Website domain
- Extracted email addresses
- Social media presence

Respond ONLY with a valid JSON object. No markdown, no explanation outside the JSON.

Format:
{
  "verified_email": "<the single best email or null>",
  "email_belongs_to_business": <true|false|null>,
  "quality_score": "<hot|warm|cold>",
  "reasoning": "<1-2 sentence explanation>"
}

Scoring guide:
- hot: Business email confirmed, website present, social signals strong → real decision-maker reachable
- warm: Partial match (generic email like info@, no domain match, or missing social)
- cold: No email, mismatched domain, or clearly not the business contact
"""


async def verify_lead(
    business_name: str,
    category: Optional[str],
    website_url: Optional[str],
    emails: list,
    social_links: dict,
) -> dict:
    """
    Use Gemini Flash to verify lead emails and assign a quality score.
    Returns dict: {verified_email, email_belongs_to_business, quality_score, reasoning}
    """
    if not settings.GEMINI_API_KEY:
        logger.warning("No GEMINI_API_KEY set — returning default cold score")
        return _default_result()

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=_MODEL_NAME,
        system_instruction=_SYSTEM_PROMPT,
    )

    domain = ""
    if website_url:
        try:
            from urllib.parse import urlparse
            domain = urlparse(website_url).netloc.lstrip("www.")
        except Exception:
            pass

    user_message = f"""Business: {business_name}
Category: {category or "Unknown"}
Website domain: {domain or "Not available"}
Extracted emails: {", ".join(emails) if emails else "None found"}
Social media: {json.dumps(social_links) if social_links else "None found"}
"""

    try:
        response = await model.generate_content_async(user_message)
        text = response.text.strip()

        # Strip markdown code fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text).strip()
        text = re.sub(r"\s*```$", "", text).strip()

        result = json.loads(text)
        return {
            "verified_email": result.get("verified_email"),
            "email_belongs_to_business": result.get("email_belongs_to_business"),
            "quality_score": result.get("quality_score", "cold"),
            "ai_reasoning": result.get("reasoning", ""),
        }

    except json.JSONDecodeError as e:
        logger.error(f"Gemini JSON parse error: {e} — raw: {text[:200]}")
        return _default_result()
    except Exception as e:
        logger.error(f"Gemini API error: {e}", exc_info=True)
        return _default_result()


def _default_result() -> dict:
    return {
        "verified_email": None,
        "email_belongs_to_business": None,
        "quality_score": "cold",
        "ai_reasoning": "Verification skipped — API unavailable or no key configured.",
    }
