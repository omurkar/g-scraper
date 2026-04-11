"""FastAPI route handlers for the LeadScout API."""

import asyncio
import csv
import io
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models.db_models import SearchJob, Lead, EnrichmentData, Verification
from models.schemas import (
    SearchRequest, SearchJobOut, SearchJobDetail,
    LeadListOut, LeadOut, SearchJobListOut
)
from services.scraper import scrape_google_maps
from services.enricher import enrich_leads_batch
from services.verifier import verify_lead
from api.websocket import manager

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Health Check ─────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "ok", "service": "LeadScout API"}


# ─── Search Jobs ──────────────────────────────────────────────────────────────

@router.post("/api/search", response_model=SearchJobOut)
async def create_search(
    body: SearchRequest,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Start a new Google Maps search job."""
    job = SearchJob(
        keyword=body.keyword,
        location=body.location,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    bg.add_task(run_full_pipeline, job.id, body.keyword, body.location, body.max_results)
    logger.info(f"Created job {job.id}: '{body.keyword}' in '{body.location}'")
    return job


@router.get("/api/jobs", response_model=SearchJobListOut)
def list_jobs(db: Session = Depends(get_db)):
    """Return all search jobs, newest first."""
    jobs = db.query(SearchJob).order_by(SearchJob.created_at.desc()).all()
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/api/search/{job_id}", response_model=SearchJobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.delete("/api/search/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    db.delete(job)
    db.commit()
    return {"deleted": job_id}


# ─── Leads ────────────────────────────────────────────────────────────────────

@router.get("/api/search/{job_id}/leads", response_model=LeadListOut)
def get_leads(
    job_id: str,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    total = db.query(Lead).filter(Lead.search_job_id == job_id).count()
    leads = (
        db.query(Lead)
        .filter(Lead.search_job_id == job_id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"leads": leads, "total": total, "page": page, "page_size": page_size}


# ─── CSV Export ───────────────────────────────────────────────────────────────

@router.get("/api/search/{job_id}/export")
def export_csv(job_id: str, db: Session = Depends(get_db)):
    job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    leads = db.query(Lead).filter(Lead.search_job_id == job_id).all()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "business_name", "category", "address", "phone", "rating", "review_count",
        "website_url", "google_maps_url",
        "emails", "linkedin_url", "instagram_url", "facebook_url", "twitter_url",
        "quality_score", "verified_email", "email_belongs_to_business", "ai_reasoning",
    ])
    writer.writeheader()
    for lead in leads:
        row = {
            "business_name": lead.business_name,
            "category": lead.category or "",
            "address": lead.address or "",
            "phone": lead.phone or "",
            "rating": lead.rating or "",
            "review_count": lead.review_count or "",
            "website_url": lead.website_url or "",
            "google_maps_url": lead.google_maps_url or "",
            "emails": "",
            "linkedin_url": "",
            "instagram_url": "",
            "facebook_url": "",
            "twitter_url": "",
            "quality_score": "",
            "verified_email": "",
            "email_belongs_to_business": "",
            "ai_reasoning": "",
        }
        if lead.enrichment:
            row["emails"] = "; ".join(lead.enrichment.emails or [])
            row["linkedin_url"] = lead.enrichment.linkedin_url or ""
            row["instagram_url"] = lead.enrichment.instagram_url or ""
            row["facebook_url"] = lead.enrichment.facebook_url or ""
            row["twitter_url"] = lead.enrichment.twitter_url or ""
        if lead.verification:
            row["quality_score"] = lead.verification.quality_score or ""
            row["verified_email"] = lead.verification.verified_email or ""
            row["email_belongs_to_business"] = str(lead.verification.email_belongs_to_business or "")
            row["ai_reasoning"] = lead.verification.ai_reasoning or ""
        writer.writerow(row)

    output.seek(0)
    filename = f"leadscout_{job.keyword}_{job.location}.csv".replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── WebSocket ────────────────────────────────────────────────────────────────

@router.websocket("/api/ws/{job_id}")
async def websocket_endpoint(job_id: str, ws: WebSocket):
    await manager.connect(job_id, ws)
    try:
        while True:
            # Keep alive — client can send pings
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(job_id, ws)


# ─── Background Pipeline ──────────────────────────────────────────────────────

async def run_full_pipeline(job_id: str, keyword: str, location: str, max_results: int):
    """Full scrape → enrich → verify pipeline as a background task."""
    from database import SessionLocal
    db = SessionLocal()

    async def _broadcast(payload: dict):
        await manager.broadcast(job_id, payload)

    try:
        # ── Phase 1: Scraping ──────────────────────────────────────────────
        _update_job(db, job_id, status="scraping")
        await _broadcast({"type": "status", "status": "scraping"})

        scraped_leads = []

        def _on_scraped(data: dict):
            nonlocal scraped_leads
            # Save lead to DB immediately (sync)
            lead = Lead(
                search_job_id=job_id,
                business_name=data["lead"]["business_name"],
                address=data["lead"].get("address"),
                phone=data["lead"].get("phone"),
                rating=data["lead"].get("rating"),
                review_count=data["lead"].get("review_count"),
                website_url=data["lead"].get("website_url"),
                google_maps_url=data["lead"].get("google_maps_url"),
                category=data["lead"].get("category"),
                status="scraped",
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)
            scraped_leads.append({"id": lead.id, "website_url": lead.website_url})
            # Update job progress
            job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
            if job:
                job.total_results = data["count"]
                job.processed_results = data["count"]
                db.commit()
            asyncio.get_event_loop().run_until_complete(
                _broadcast({"type": "lead_scraped", "lead": _lead_to_dict(lead), "total": data["count"]})
            ) if False else None  # WS broadcast from sync context — done async below

        # Run scraper in a thread executor to avoid blocking event loop
        loop = asyncio.get_event_loop()

        raw_leads = await scrape_google_maps(
            keyword=keyword,
            location=location,
            max_results=max_results,
        )

        # Persist all scraped leads
        for raw in raw_leads:
            lead = Lead(
                search_job_id=job_id,
                business_name=raw["business_name"] or "Unknown",
                address=raw.get("address"),
                phone=raw.get("phone"),
                rating=raw.get("rating"),
                review_count=raw.get("review_count"),
                website_url=raw.get("website_url"),
                google_maps_url=raw.get("google_maps_url"),
                category=raw.get("category"),
                status="scraped",
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)
            scraped_leads.append({"id": lead.id, "website_url": lead.website_url})

        _update_job(db, job_id, status="enriching", total=len(raw_leads))
        await _broadcast({"type": "status", "status": "enriching", "total": len(raw_leads)})

        # ── Phase 2: Enrichment ────────────────────────────────────────────
        enriched = await enrich_leads_batch(scraped_leads)

        for entry in enriched:
            lead_id = entry["lead_id"]
            enr_data = entry["enrichment"]

            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                continue

            enr = EnrichmentData(
                lead_id=lead_id,
                emails=enr_data.get("emails", []),
                social_links=enr_data.get("social_links", {}),
                linkedin_url=enr_data.get("linkedin_url"),
                instagram_url=enr_data.get("instagram_url"),
                facebook_url=enr_data.get("facebook_url"),
                twitter_url=enr_data.get("twitter_url"),
            )
            db.add(enr)
            lead.status = "enriched"
            db.commit()

            await _broadcast({"type": "lead_enriched", "lead_id": lead_id, "emails": enr_data.get("emails", [])})

        _update_job(db, job_id, status="verifying")
        await _broadcast({"type": "status", "status": "verifying"})

        # ── Phase 3: AI Verification ───────────────────────────────────────
        leads_in_db = db.query(Lead).filter(Lead.search_job_id == job_id).all()
        for lead in leads_in_db:
            emails = []
            social_links = {}
            if lead.enrichment:
                emails = lead.enrichment.emails or []
                social_links = lead.enrichment.social_links or {}

            ver_result = await verify_lead(
                business_name=lead.business_name,
                category=lead.category,
                website_url=lead.website_url,
                emails=emails,
                social_links=social_links,
            )

            ver = Verification(
                lead_id=lead.id,
                verified_email=ver_result.get("verified_email"),
                quality_score=ver_result.get("quality_score"),
                ai_reasoning=ver_result.get("ai_reasoning"),
                email_belongs_to_business=ver_result.get("email_belongs_to_business"),
            )
            db.add(ver)
            lead.status = "verified"
            db.commit()

            await _broadcast({
                "type": "lead_verified",
                "lead_id": lead.id,
                "quality_score": ver_result.get("quality_score"),
            })

        _update_job(db, job_id, status="completed")
        await _broadcast({"type": "status", "status": "completed"})
        logger.info(f"Job {job_id} completed. {len(raw_leads)} leads processed.")

    except Exception as e:
        logger.error(f"Pipeline failed for job {job_id}: {e}", exc_info=True)
        _update_job(db, job_id, status="failed", error=str(e))
        await _broadcast({"type": "status", "status": "failed", "error": str(e)})
    finally:
        db.close()


def _update_job(db, job_id: str, status: str, total: int = None, error: str = None):
    job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
    if job:
        job.status = status
        if total is not None:
            job.total_results = total
        if error:
            job.error_message = error
        db.commit()


def _lead_to_dict(lead) -> dict:
    return {
        "id": lead.id,
        "business_name": lead.business_name,
        "address": lead.address,
        "phone": lead.phone,
        "rating": lead.rating,
        "review_count": lead.review_count,
        "website_url": lead.website_url,
        "category": lead.category,
        "status": lead.status,
    }
