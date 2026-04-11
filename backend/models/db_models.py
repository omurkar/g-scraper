"""SQLAlchemy ORM models for LeadScout."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, JSON
)
from sqlalchemy.orm import relationship

from database import Base


def _uuid():
    return str(uuid.uuid4())


class SearchJob(Base):
    __tablename__ = "search_jobs"

    id = Column(String, primary_key=True, default=_uuid)
    keyword = Column(String, nullable=False)
    location = Column(String, nullable=False)
    status = Column(String, default="pending")      # pending|scraping|enriching|verifying|completed|failed
    total_results = Column(Integer, default=0)
    processed_results = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    leads = relationship("Lead", back_populates="search_job", cascade="all, delete-orphan")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(String, primary_key=True, default=_uuid)
    search_job_id = Column(String, ForeignKey("search_jobs.id"), nullable=False)
    business_name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)
    website_url = Column(String, nullable=True)
    google_maps_url = Column(String, nullable=True)
    category = Column(String, nullable=True)
    status = Column(String, default="scraped")      # scraped|enriching|enriched|verified
    created_at = Column(DateTime, default=datetime.utcnow)

    search_job = relationship("SearchJob", back_populates="leads")
    enrichment = relationship("EnrichmentData", back_populates="lead", uselist=False, cascade="all, delete-orphan")
    verification = relationship("Verification", back_populates="lead", uselist=False, cascade="all, delete-orphan")


class EnrichmentData(Base):
    __tablename__ = "enrichment_data"

    id = Column(String, primary_key=True, default=_uuid)
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False)
    emails = Column(JSON, default=list)
    social_links = Column(JSON, default=dict)
    linkedin_url = Column(String, nullable=True)
    instagram_url = Column(String, nullable=True)
    facebook_url = Column(String, nullable=True)
    twitter_url = Column(String, nullable=True)
    enriched_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="enrichment")


class Verification(Base):
    __tablename__ = "verifications"

    id = Column(String, primary_key=True, default=_uuid)
    lead_id = Column(String, ForeignKey("leads.id"), nullable=False)
    verified_email = Column(String, nullable=True)
    quality_score = Column(String, nullable=True)           # hot|warm|cold
    ai_reasoning = Column(Text, nullable=True)
    email_belongs_to_business = Column(Boolean, nullable=True)
    verified_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="verification")
