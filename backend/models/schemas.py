"""Pydantic request/response schemas — v2 with locality, lead_goal, health audit."""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


# ─── Request Models ──────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    keyword: str                                        # single category for simple search
    location: str                                       # city
    max_results: int = Field(30, ge=1, le=500)
    # New bulk/locality fields
    categories: List[str] = []                         # multi-category (empty = use keyword)
    localities: List[str] = []                         # locality names (empty = whole city)
    lead_goal: int = Field(30, ge=1, le=2000)          # stop after this many total leads
    select_all_localities: bool = False                 # sweep every locality in city


# ─── Response Models ─────────────────────────────────────────────────────────

class VerificationOut(BaseModel):
    id: str
    verified_email: Optional[str]
    quality_score: Optional[str]
    ai_reasoning: Optional[str]
    email_belongs_to_business: Optional[bool]
    verified_at: Optional[datetime]

    class Config:
        from_attributes = True


class EnrichmentOut(BaseModel):
    id: str
    emails: Optional[List[str]] = []
    social_links: Optional[Dict[str, Any]] = {}
    linkedin_url: Optional[str]
    instagram_url: Optional[str]
    facebook_url: Optional[str]
    twitter_url: Optional[str]
    enriched_at: Optional[datetime]

    class Config:
        from_attributes = True


class LeadOut(BaseModel):
    id: str
    search_job_id: str
    business_name: str
    address: Optional[str]
    phone: Optional[str]
    rating: Optional[float]
    review_count: Optional[int]
    website_url: Optional[str]
    google_maps_url: Optional[str]
    category: Optional[str]
    locality: Optional[str]
    status: str
    # Health audit
    website_tag: Optional[str]                         # NO_SITE | FIX_NEEDED | GOOD_SITE
    ssl_ok: Optional[bool]
    load_time_ms: Optional[int]
    mobile_friendly: Optional[bool]
    http_status: Optional[int]
    health_issues: Optional[List[str]] = []
    created_at: datetime
    enrichment: Optional[EnrichmentOut] = None
    verification: Optional[VerificationOut] = None

    class Config:
        from_attributes = True


class SearchJobOut(BaseModel):
    id: str
    keyword: str
    location: str
    localities: Optional[List[str]] = []
    categories: Optional[List[str]] = []
    lead_goal: Optional[int]
    status: str
    total_results: int
    processed_results: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SearchJobListOut(BaseModel):
    jobs: List[SearchJobOut]
    total: int


class LeadListOut(BaseModel):
    leads: List[LeadOut]
    total: int
    page: int
    page_size: int
    # Aggregate counts for the filter bar
    count_no_site: int = 0
    count_fix_needed: int = 0
    count_good_site: int = 0


# ─── Locality API models ─────────────────────────────────────────────────────

class LocalityRegion(BaseModel):
    region: str
    localities: List[Dict[str, str]]     # [{name, query}]


class CityLocalitiesOut(BaseModel):
    city: str
    regions: List[LocalityRegion]
    total_localities: int


class KeywordPreviewOut(BaseModel):
    keywords: List[str]
    total: int
