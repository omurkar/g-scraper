"""FastAPI routes — v2: bulk search, locality engine, health audit, segmented exports."""

import asyncio
import csv
import io
import logging
from typing import Optional, List
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models.db_models import SearchJob, Lead, EnrichmentData, Verification
from models.schemas import (
    SearchRequest, SearchJobOut, LeadListOut, LeadOut,
    SearchJobListOut, CityLocalitiesOut, LocalityRegion, KeywordPreviewOut
)
from services.scraper import scrape_google_maps
from services.enricher import enrich_leads_batch
from services.verifier import verify_lead
from services.health_checker import audit_leads_batch
from data.localities import (
    CITY_LOCALITIES, GMB_CATEGORIES, SUPPORTED_CITIES,
    get_all_locality_queries, get_all_queries
)
from api.websocket import manager

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Health ───────────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "ok", "service": "LeadScout API v2"}


# ─── Locality Engine endpoints ─────────────────────────────────────────────────

@router.get("/api/cities", response_model=List[str])
def get_cities():
    """List all supported cities."""
    return SUPPORTED_CITIES


@router.get("/api/cities/{city}/localities", response_model=CityLocalitiesOut)
def get_city_localities(city: str):
    """Return all localities for a city grouped by region."""
    if city not in CITY_LOCALITIES:
        raise HTTPException(404, f"City '{city}' not in locality database")
    regions_data = CITY_LOCALITIES[city]
    regions = [
        LocalityRegion(region=region, localities=locs)
        for region, locs in regions_data.items()
    ]
    total = sum(len(r.localities) for r in regions)
    return CityLocalitiesOut(city=city, regions=regions, total_localities=total)


@router.get("/api/categories", response_model=List[str])
def get_categories():
    """Return the list of preset GMB categories."""
    return GMB_CATEGORIES


@router.post("/api/keyword-preview", response_model=KeywordPreviewOut)
def preview_keywords(body: SearchRequest):
    """
    Return the list of search keywords that will be generated
    for the given categories + city + localities — without running a search.
    """
    keywords = _build_keyword_list(body)
    return KeywordPreviewOut(keywords=keywords, total=len(keywords))


# ─── Search Jobs ───────────────────────────────────────────────────────────────

@router.post("/api/search", response_model=SearchJobOut)
async def create_search(
    body: SearchRequest,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Start a new bulk search job."""
    # Use first category as keyword display, or the keyword field
    display_keyword = body.keyword
    if body.categories:
        display_keyword = ", ".join(body.categories[:3])
        if len(body.categories) > 3:
            display_keyword += f" +{len(body.categories)-3} more"

    job = SearchJob(
        keyword=display_keyword,
        location=body.location,
        localities=body.localities,
        categories=body.categories,
        lead_goal=body.lead_goal,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    bg.add_task(run_bulk_pipeline, job.id, body)
    logger.info(f"Created job {job.id}: '{display_keyword}' in '{body.location}' (goal: {body.lead_goal})")
    return job


@router.get("/api/jobs", response_model=SearchJobListOut)
def list_jobs(db: Session = Depends(get_db)):
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
    page_size: int = 100,
    tag: Optional[str] = Query(None, description="Filter: NO_SITE | FIX_NEEDED | GOOD_SITE"),
    db: Session = Depends(get_db),
):
    job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    q = db.query(Lead).filter(Lead.search_job_id == job_id)
    if tag:
        q = q.filter(Lead.website_tag == tag)

    total = q.count()
    leads = q.offset((page - 1) * page_size).limit(page_size).all()

    # Get counts per tag for the filter bar
    all_leads_q = db.query(Lead).filter(Lead.search_job_id == job_id)
    count_no_site   = all_leads_q.filter(Lead.website_tag == "NO_SITE").count()
    count_fix       = all_leads_q.filter(Lead.website_tag == "FIX_NEEDED").count()
    count_good      = all_leads_q.filter(Lead.website_tag == "GOOD_SITE").count()

    return {
        "leads": leads,
        "total": total,
        "page": page,
        "page_size": page_size,
        "count_no_site": count_no_site,
        "count_fix_needed": count_fix,
        "count_good_site": count_good,
    }


# ─── Segmented CSV Exports ────────────────────────────────────────────────────

@router.get("/api/search/{job_id}/export")
def export_csv(
    job_id: str,
    tag: Optional[str] = Query(None, description="all | NO_SITE | FIX_NEEDED | GOOD_SITE"),
    db: Session = Depends(get_db),
):
    """Export leads to CSV. Use ?tag= to filter by website health tag."""
    job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    q = db.query(Lead).filter(Lead.search_job_id == job_id)
    if tag and tag != "all":
        q = q.filter(Lead.website_tag == tag)
    leads = q.all()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "business_name", "category", "locality", "address", "phone",
        "rating", "review_count",
        "website_url", "google_maps_url",
        "website_tag", "ssl_ok", "load_time_ms", "mobile_friendly", "health_issues",
        "emails", "linkedin_url", "instagram_url", "facebook_url", "twitter_url",
        "quality_score", "verified_email", "email_belongs_to_business", "ai_reasoning",
    ])
    writer.writeheader()

    for lead in leads:
        issues_str = "; ".join(lead.health_issues or [])
        row = {
            "business_name": lead.business_name,
            "category": lead.category or "",
            "locality": lead.locality or "",
            "address": lead.address or "",
            "phone": lead.phone or "",
            "rating": lead.rating or "",
            "review_count": lead.review_count or "",
            "website_url": lead.website_url or "",
            "google_maps_url": lead.google_maps_url or "",
            "website_tag": lead.website_tag or "",
            "ssl_ok": str(lead.ssl_ok) if lead.ssl_ok is not None else "",
            "load_time_ms": lead.load_time_ms or "",
            "mobile_friendly": str(lead.mobile_friendly) if lead.mobile_friendly is not None else "",
            "health_issues": issues_str,
            "emails": "; ".join(lead.enrichment.emails or []) if lead.enrichment else "",
            "linkedin_url": lead.enrichment.linkedin_url or "" if lead.enrichment else "",
            "instagram_url": lead.enrichment.instagram_url or "" if lead.enrichment else "",
            "facebook_url": lead.enrichment.facebook_url or "" if lead.enrichment else "",
            "twitter_url": lead.enrichment.twitter_url or "" if lead.enrichment else "",
            "quality_score": lead.verification.quality_score or "" if lead.verification else "",
            "verified_email": lead.verification.verified_email or "" if lead.verification else "",
            "email_belongs_to_business": str(lead.verification.email_belongs_to_business or "") if lead.verification else "",
            "ai_reasoning": lead.verification.ai_reasoning or "" if lead.verification else "",
        }
        writer.writerow(row)

    output.seek(0)
    tag_suffix = f"_{tag}" if tag and tag != "all" else ""
    filename = f"leadscout_{job.keyword}_{job.location}{tag_suffix}.csv".replace(" ", "_").replace(",", "")
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── WebSocket ─────────────────────────────────────────────────────────────────

@router.websocket("/api/ws/{job_id}")
async def websocket_endpoint(job_id: str, ws: WebSocket):
    await manager.connect(job_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(job_id, ws)


# ─── Drop & Go: Upload .txt file and start scraping ───────────────────────────

@router.post("/api/upload-keywords")
async def upload_keywords(
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    lead_goal: int = Query(default=100, ge=1, le=5000),
    location: str = Query(default="India"),
):
    """
    Drop & Go: Parse a .txt file (one keyword per line) and immediately
    launch a scraping job. Each line becomes a unique search query.
    Returns the job_id so the client can connect to its WebSocket.
    """
    if not file.filename.endswith(".txt"):
        raise HTTPException(400, "Only .txt files are accepted")

    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1", errors="ignore")

    # Parse lines: strip whitespace, skip empty / commented lines
    lines = [ln.strip() for ln in text.splitlines()]
    keywords = [ln for ln in lines if ln and not ln.startswith("#")]

    if not keywords:
        raise HTTPException(400, "No valid keywords found in the file")

    logger.info(f"Upload: {len(keywords)} keywords from '{file.filename}'")

    # Build a synthetic SearchRequest using file keywords as raw queries
    # We store the full keyword list in the job;
    # the pipeline will treat each line as a standalone search string.
    display_keyword = f"{keywords[0]} +{len(keywords)-1} more" if len(keywords) > 1 else keywords[0]

    job = SearchJob(
        keyword=display_keyword,
        location=location,
        localities=[],
        categories=keywords,   # store raw queries in the categories JSON column
        lead_goal=lead_goal,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    bg.add_task(run_keyword_file_pipeline, job.id, keywords, lead_goal)
    return {
        "job_id": job.id,
        "total_keywords": len(keywords),
        "lead_goal": lead_goal,
        "status": "pending",
        "message": f"{len(keywords)} keywords queued — scraping will begin shortly",
    }


# ─── Bulk Pipeline ─────────────────────────────────────────────────────────────

def _build_keyword_list(body: SearchRequest) -> List[str]:
    """Generate [Category] in [Locality/City] search strings."""
    categories = body.categories if body.categories else [body.keyword]

    if body.select_all_localities and body.location in CITY_LOCALITIES:
        location_queries = get_all_queries(body.location)
    elif body.localities:
        location_queries = get_all_locality_queries(body.location, body.localities)
    else:
        location_queries = [body.location]

    keywords = []
    for cat in categories:
        for loc in location_queries:
            keywords.append(f"{cat} in {loc}")
    return keywords


async def run_bulk_pipeline(job_id: str, body: SearchRequest):
    """
    Bulk pipeline:
      1. Generate keyword × locality combos
      2. Scrape each combo until lead_goal is hit
      3. Health-check all leads
      4. Enrich leads that have websites
      5. AI verify
    """
    from database import SessionLocal
    db = SessionLocal()

    async def _broadcast(payload: dict):
        await manager.broadcast(job_id, payload)

    try:
        keywords = _build_keyword_list(body)
        logger.info(f"Job {job_id}: {len(keywords)} keyword combos, goal={body.lead_goal}")
        await _broadcast({"type": "keywords_ready", "total_keywords": len(keywords), "keywords": keywords[:20]})

        # ── Phase 1: Scraping ────────────────────────────────────────────────
        _update_job(db, job_id, status="scraping")
        await _broadcast({"type": "status", "status": "scraping"})

        all_scraped: List[dict] = []   # raw dicts from scraper
        scraped_lead_ids: List[dict] = []  # {id, website_url} for health + enrichment

        per_keyword_limit = max(5, body.lead_goal // max(len(keywords), 1) + 2)

        for kw_index, keyword in enumerate(keywords):
            if len(all_scraped) >= body.lead_goal:
                break

            # keyword = "Dentist in Andheri East, Mumbai"
            parts = keyword.split(" in ", 1)
            category = parts[0].strip()
            location_query = parts[1].strip() if len(parts) > 1 else body.location
            # Determine locality name from the query
            locality_name = location_query.split(",")[0].strip() if "," in location_query else location_query

            logger.info(f"[{kw_index+1}/{len(keywords)}] Scraping: {keyword}")
            await _broadcast({"type": "scraping_keyword", "keyword": keyword, "index": kw_index+1, "total": len(keywords)})

            try:
                raw_leads = await scrape_google_maps(
                    keyword=category,
                    location=location_query,
                    max_results=per_keyword_limit,
                )
            except Exception as e:
                logger.warning(f"Scraper error for '{keyword}': {e}")
                raw_leads = []

            for raw in raw_leads:
                if len(all_scraped) >= body.lead_goal:
                    break
                if not raw.get("business_name"):
                    continue

                lead = Lead(
                    search_job_id=job_id,
                    business_name=raw["business_name"][:255],
                    address=raw.get("address"),
                    phone=raw.get("phone"),
                    rating=raw.get("rating"),
                    review_count=raw.get("review_count"),
                    website_url=raw.get("website_url"),
                    google_maps_url=raw.get("google_maps_url"),
                    category=category,
                    locality=locality_name,
                    status="scraped",
                )
                db.add(lead)
                db.commit()
                db.refresh(lead)
                all_scraped.append(raw)
                scraped_lead_ids.append({"id": lead.id, "website_url": lead.website_url})

                _update_job(db, job_id, total=len(all_scraped))
                await _broadcast({
                    "type": "lead_scraped",
                    "lead": {
                        "id": lead.id, "business_name": lead.business_name,
                        "category": category, "locality": locality_name,
                        "website_url": lead.website_url,
                    },
                    "total": len(all_scraped),
                })

        logger.info(f"Scraping done: {len(all_scraped)} leads")

        # ── Phase 2: Website Health Check ────────────────────────────────────
        _update_job(db, job_id, status="health_check")
        await _broadcast({"type": "status", "status": "health_check", "total": len(all_scraped)})

        health_results = await audit_leads_batch(scraped_lead_ids, max_concurrent=10)

        for lead_id, audit in health_results.items():
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                continue
            lead.website_tag = audit["website_tag"]
            lead.ssl_ok = audit["ssl_ok"]
            lead.load_time_ms = audit["load_time_ms"]
            lead.mobile_friendly = audit["mobile_friendly"]
            lead.http_status = audit["http_status"]
            lead.health_issues = audit["health_issues"]
            lead.status = "health_checked"
            db.commit()
            await _broadcast({
                "type": "lead_health",
                "lead_id": lead_id,
                "website_tag": audit["website_tag"],
                "issues": audit["health_issues"],
            })

        # ── Phase 3: Enrichment ──────────────────────────────────────────────
        # Only enrich leads that HAVE a website (no point visiting NO_SITE leads)
        enrichable = [l for l in scraped_lead_ids if l.get("website_url")]
        if enrichable:
            _update_job(db, job_id, status="enriching")
            await _broadcast({"type": "status", "status": "enriching"})

            enriched = await enrich_leads_batch(enrichable)
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

        # ── Phase 4: AI Verification ─────────────────────────────────────────
        _update_job(db, job_id, status="verifying")
        await _broadcast({"type": "status", "status": "verifying"})

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
        await _broadcast({"type": "status", "status": "completed", "total": len(all_scraped)})
        logger.info(f"Job {job_id} complete — {len(all_scraped)} leads")

    except Exception as e:
        logger.error(f"Pipeline failed [{job_id}]: {e}", exc_info=True)
        _update_job(db, job_id, status="failed", error=str(e))
        await _broadcast({"type": "status", "status": "failed", "error": str(e)})
    finally:
        db.close()


# ─── Keyword-file Pipeline ────────────────────────────────────────────────────

async def run_keyword_file_pipeline(
    job_id: str,
    keywords: List[str],
    lead_goal: int,
    batch_size: int = 5,
):
    """
    Parallel-batch pipeline for Drop & Go uploads.
    • Splits keywords into batches of `batch_size`
    • Runs each batch concurrently to maximise speed
    • Broadcasts fine-grained progress events over WebSocket
    """
    from database import SessionLocal
    db = SessionLocal()

    async def _broadcast(payload: dict):
        await manager.broadcast(job_id, payload)

    try:
        total_kw = len(keywords)
        logger.info(f"File pipeline [{job_id}]: {total_kw} keywords, goal={lead_goal}, batch={batch_size}")

        await _broadcast({
            "type": "file_job_started",
            "total_keywords": total_kw,
            "lead_goal": lead_goal,
        })

        _update_job(db, job_id, status="scraping")
        await _broadcast({"type": "status", "status": "scraping"})

        all_scraped: List[dict] = []
        scraped_lead_ids: List[dict] = []
        per_keyword_limit = max(5, lead_goal // max(total_kw, 1) + 2)
        completed_keywords = 0

        # ── Batch processing ──────────────────────────────────────────────
        for batch_start in range(0, total_kw, batch_size):
            if len(all_scraped) >= lead_goal:
                break

            batch = keywords[batch_start: batch_start + batch_size]

            async def _scrape_one(kw: str):
                """Scrape a single raw query string."""
                # Heuristic split: "[category] in [location]" → keep as-is for scraper
                # If no " in " found, append the job location
                if " in " in kw.lower():
                    parts = kw.split(" in ", 1)
                    cat = parts[0].strip()
                    loc = parts[1].strip()
                else:
                    cat = kw
                    loc = "India"  # default fallback
                locality_name = loc.split(",")[0].strip() if "," in loc else loc
                try:
                    raw_leads = await scrape_google_maps(
                        keyword=cat,
                        location=loc,
                        max_results=per_keyword_limit,
                    )
                    return cat, locality_name, raw_leads
                except Exception as exc:
                    logger.warning(f"Scraper error for '{kw}': {exc}")
                    return cat, locality_name, []

            batch_results = await asyncio.gather(*[_scrape_one(kw) for kw in batch])

            for cat, locality_name, raw_leads in batch_results:
                if len(all_scraped) >= lead_goal:
                    break
                for raw in raw_leads:
                    if len(all_scraped) >= lead_goal:
                        break
                    if not raw.get("business_name"):
                        continue

                    lead = Lead(
                        search_job_id=job_id,
                        business_name=raw["business_name"][:255],
                        address=raw.get("address"),
                        phone=raw.get("phone"),
                        rating=raw.get("rating"),
                        review_count=raw.get("review_count"),
                        website_url=raw.get("website_url"),
                        google_maps_url=raw.get("google_maps_url"),
                        category=cat,
                        locality=locality_name,
                        status="scraped",
                    )
                    db.add(lead)
                    db.commit()
                    db.refresh(lead)
                    all_scraped.append(raw)
                    scraped_lead_ids.append({"id": lead.id, "website_url": lead.website_url})
                    _update_job(db, job_id, total=len(all_scraped))

            completed_keywords += len(batch)
            pct = round(completed_keywords / total_kw * 100)
            await _broadcast({
                "type": "file_progress",
                "completed_keywords": completed_keywords,
                "total_keywords": total_kw,
                "leads_found": len(all_scraped),
                "pct": pct,
            })

        logger.info(f"File-pipeline scraping done: {len(all_scraped)} leads")

        # ── Health check ──────────────────────────────────────────────────
        _update_job(db, job_id, status="health_check")
        await _broadcast({"type": "status", "status": "health_check", "total": len(all_scraped)})

        health_results = await audit_leads_batch(scraped_lead_ids, max_concurrent=10)
        for lead_id, audit in health_results.items():
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                continue
            lead.website_tag = audit["website_tag"]
            lead.ssl_ok = audit["ssl_ok"]
            lead.load_time_ms = audit["load_time_ms"]
            lead.mobile_friendly = audit["mobile_friendly"]
            lead.http_status = audit["http_status"]
            lead.health_issues = audit["health_issues"]
            lead.status = "health_checked"
            db.commit()
            await _broadcast({
                "type": "lead_health",
                "lead_id": lead_id,
                "website_tag": audit["website_tag"],
                "issues": audit["health_issues"],
            })

        # ── Enrichment ────────────────────────────────────────────────────
        enrichable = [l for l in scraped_lead_ids if l.get("website_url")]
        if enrichable:
            _update_job(db, job_id, status="enriching")
            await _broadcast({"type": "status", "status": "enriching"})
            enriched = await enrich_leads_batch(enrichable)
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

        # ── Mark completed ────────────────────────────────────────────────
        _update_job(db, job_id, status="completed")
        await _broadcast({
            "type": "status",
            "status": "completed",
            "total": len(all_scraped),
            "is_file_job": True,
        })
        logger.info(f"File pipeline [{job_id}] complete — {len(all_scraped)} leads")

    except Exception as e:
        logger.error(f"File pipeline failed [{job_id}]: {e}", exc_info=True)
        _update_job(db, job_id, status="failed", error=str(e))
        await _broadcast({"type": "status", "status": "failed", "error": str(e)})
    finally:
        db.close()


def _update_job(db, job_id: str, status: str = None, total: int = None, error: str = None):
    job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
    if job:
        if status: job.status = status
        if total is not None: job.total_results = total
        if error: job.error_message = error
        db.commit()
