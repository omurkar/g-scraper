"""Pydantic request/response schemas for the LeadScout API."""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel


# ─── Request Models ──────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    keyword: str
    location: str
    max_results: int = 30


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
    status: str
    created_at: datetime
    enrichment: Optional[EnrichmentOut] = None
    verification: Optional[VerificationOut] = None

    class Config:
        from_attributes = True


class SearchJobOut(BaseModel):
    id: str
    keyword: str
    location: str
    status: str
    total_results: int
    processed_results: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SearchJobDetail(SearchJobOut):
    leads: List[LeadOut] = []


class SearchJobListOut(BaseModel):
    jobs: List[SearchJobOut]
    total: int


class LeadListOut(BaseModel):
    leads: List[LeadOut]
    total: int
    page: int
    page_size: int
