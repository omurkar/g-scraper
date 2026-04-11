# 📋 LeadScout — Task Tracker

> Master checklist for the Lead Generation MVP build.  
> Status: ⬜ Not Started | 🔄 In Progress | ✅ Done | ❌ Blocked

---

## Phase 1: The Scraper ⛏️ — ✅ COMPLETE

### 1.1 — Project Scaffolding ✅
- [x] Create backend directory structure (`backend/models/`, `backend/api/`, `backend/services/`, `backend/utils/`)
- [x] Create `requirements.txt` with FastAPI, Playwright, SQLAlchemy, uvicorn
- [x] Create `backend/main.py` — FastAPI app with CORS + health check + lifespan DB init
- [x] Create `backend/config.py` — Environment variables loader with SQLite/Postgres support
- [x] Create all `__init__.py` files
- [x] Initialize Next.js 16 frontend with Tailwind CSS + Lucide Icons
- [x] Create `docker-compose.yml` for PostgreSQL (optional — SQLite default)

### 1.2 — Database Setup ✅
- [x] Create `backend/models/db_models.py` — SQLAlchemy ORM: SearchJob, Lead, EnrichmentData, Verification
- [x] Create `backend/models/schemas.py` — Pydantic request/response models
- [x] Create `backend/database.py` — SQLAlchemy engine + session factory (SQLite + PostgreSQL)
- [x] Tables auto-created on startup via `init_db()`

### 1.3 — Google Maps Scraper ✅
- [x] Create `backend/utils/stealth.py` — UA rotation, stealth JS patches, viewport randomization
- [x] Create `backend/utils/parsers.py` — Email regex, social link patterns
- [x] Create `backend/services/scraper.py` — Core scraper
  - [x] Launch Playwright with stealth settings
  - [x] Navigate to Google Maps (homepage → type query OR direct URL fallback)
  - [x] Dismiss consent popups
  - [x] Wait for results feed
  - [x] Scroll feed to load up to 30+ results
  - [x] Collect all `/maps/place/` links
  - [x] Extract per-business: name, rating, reviews, address, phone, website, maps URL via JS eval
- [x] **Browser test**: ✅ "Dentists in Mumbai" → **30 leads found** (verified live)

### 1.4 — API Endpoints ✅
- [x] `POST /api/search` — Create job + trigger background pipeline
- [x] `GET /api/search/{id}` — Job status + metadata
- [x] `GET /api/search/{id}/leads` — Paginated leads (page, page_size)
- [x] `GET /api/search/{id}/export` — CSV download
- [x] `GET /api/jobs` — List all jobs
- [x] `DELETE /api/search/{id}` — Remove job
- [x] `GET /health` — Health check
- [x] `WS /api/ws/{job_id}` — Real-time WebSocket updates

### 1.5 — Frontend (Dashboard) ✅
- [x] `src/app/layout.tsx` — Root layout with Inter font + dark mode
- [x] `src/app/globals.css` — Full dark design system (tokens, animations, glassmorphism, badges)
- [x] `src/app/page.tsx` — Full dashboard (search, stats, job management, results)
- [x] `src/components/SearchBar.tsx` — Keyword + Location inputs + example queries + loading state
- [x] `src/components/ResultsTable.tsx` — Sortable, filterable table with quality badges + AI reasoning expand
- [x] `src/components/ProgressBar.tsx` — Phase indicator (Scraping→Enriching→Verifying→Done)
- [x] `src/components/ExportButton.tsx` — CSV download with lead count badge
- [x] `src/components/JobHistory.tsx` — Sidebar with all jobs, status badges, delete action
- [x] `src/lib/api.ts` — Typed API client (axios)
- [x] `src/lib/types.ts` — Full TypeScript interfaces
- [x] `next.config.ts` — API proxy to backend on port 8000
- [x] WebSocket real-time updates (status, lead_scraped, lead_enriched, lead_verified)
- [x] Polling fallback when WebSocket unavailable

---

## Phase 2: The Enricher 🔍 — ✅ COMPLETE

### 2.1 — Enrichment Worker ✅
- [x] Create `backend/services/enricher.py`
- [x] Create `backend/utils/parsers.py` — Email regex, social link patterns
- [x] Visit each lead's website URL with Playwright
- [x] Extract emails (regex on full HTML + mailto: links)
- [x] Auto-discover `/contact`, `/about` pages and scrape those too
- [x] Extract LinkedIn, Instagram, Facebook, Twitter/X URLs
- [x] Save enrichment data to `EnrichmentData` table
- [x] 12/30 (40%) emails extracted in live test

### 2.2 — Concurrency & Performance ✅
- [x] Semaphore-controlled concurrency (max 4 parallel browser contexts)
- [x] Image/media blocking for faster page loads
- [x] 15s timeout per website

### 2.3 — Real-time Updates ✅
- [x] Create `backend/api/websocket.py` — ConnectionManager
- [x] WebSocket broadcasts: status, lead_scraped, lead_enriched, lead_verified
- [x] Frontend ResultsTable updates live via WS messages

---

## Phase 3: AI Verification 🤖 — ✅ COMPLETE

### 3.1 — Gemini Integration ✅
- [x] Create `backend/services/verifier.py`
- [x] Gemini 2.0 Flash API client (async)
- [x] Structured JSON prompt with system instruction

### 3.2 — Quality Scoring ✅
- [x] hot/warm/cold classification
- [x] email_belongs_to_business boolean
- [x] AI reasoning text stored in Verification table
- [x] Lead status updated to "verified"

### 3.3 — UI for Verification ✅
- [x] Quality badges (HOT 🔥 / WARM / COLD) in ResultsTable
- [x] Filter by quality score (All / Hot / Warm / Cold)
- [x] AI reasoning in expandable row (click any lead to expand)

---

## Phase 4: Polish & Export ✨ — ✅ COMPLETE

### 4.1 — CSV Export ✅
- [x] `GET /api/search/{id}/export` — Full CSV with all columns
- [x] ExportButton component with lead count badge
- [x] UTF-8-BOM encoding for Excel compatibility

### 4.2 — Job Management ✅
- [x] Job history sidebar with recent jobs
- [x] Delete jobs (cascade deletes leads/enrichment/verification)
- [x] Job status badges with live spinner for active jobs

### 4.3 — Error Handling ✅
- [x] FastAPI exception handling in pipeline
- [x] Job marked as "failed" with error message on exception
- [x] Console alert when backend is unreachable

### 4.4 — UI Polish ✅
- [x] Dark theme with indigo/violet gradient palette
- [x] Glassmorphism header and search card
- [x] Smooth skeleton loaders for empty table
- [x] Animated progress bar with phase steps
- [x] Slide-in animation on each lead row
- [x] Hover effects on cards and table rows
- [x] Stats cards (total leads, emails, hot leads, status)

---

## 🔧 Next Optional Enhancements

- [ ] Add Gemini API key to `.env` for live AI verification
- [ ] Switch to PostgreSQL using docker-compose.yml
- [ ] Add proxy support in stealth.py for high-volume use
- [ ] Add pagination to ResultsTable for 100+ lead jobs
- [ ] Add retry button for failed jobs
- [ ] Add search history filtering / keyword search
- [ ] Deploy backend to Railway / Render
- [ ] Deploy frontend to Vercel

---

## Quick Start Commands

```bash
# Backend (Terminal 1)
cd backend
pip install -r requirements.txt
python -m playwright install chromium
python -m uvicorn main:app --reload --port 8000

# Frontend (Terminal 2)
cd frontend
npm install
npm run dev

# Optional: Add your Gemini API key for AI verification
# Edit backend/.env → set GEMINI_API_KEY=your-key
```

## Environment Variables

```env
# backend/.env
DATABASE_URL=sqlite:///./leadscout.db
GEMINI_API_KEY=                  # Optional — add for AI quality scoring
MAX_RESULTS_PER_SEARCH=30
SCRAPE_DELAY_MIN=2.0
SCRAPE_DELAY_MAX=4.0
PORT=8000
```
