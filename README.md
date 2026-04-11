# ⚡ LeadScout — High-Speed Lead Generation MVP

> **Search → Extract → Enrich → Verify → Export**  
> Scrapes Google Maps, enriches with emails & social links, and verifies with Gemini AI.

![Dashboard](./docs/dashboard.png)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### 1. Backend Setup

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser
python -m playwright install chromium

# Configure environment (optional - SQLite is default)
# Edit backend/.env to add your GEMINI_API_KEY

# Start the API server
python -m uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

### 3. Open Dashboard

Visit **http://localhost:3000**

---

## 🏗️ Architecture

```
LeadScout/
├── backend/
│   ├── main.py                 # FastAPI app entry + CORS + lifespan
│   ├── config.py               # Settings (SQLite/Postgres, Gemini key)
│   ├── database.py             # SQLAlchemy engine + session
│   ├── requirements.txt
│   ├── .env                    # Your secrets go here
│   ├── api/
│   │   ├── routes.py           # All REST + WebSocket endpoints
│   │   └── websocket.py        # WS connection manager
│   ├── models/
│   │   ├── db_models.py        # ORM: SearchJob, Lead, EnrichmentData, Verification
│   │   └── schemas.py          # Pydantic request/response models
│   ├── services/
│   │   ├── scraper.py          # Google Maps Playwright scraper
│   │   ├── enricher.py         # Website email/social extraction
│   │   └── verifier.py         # Gemini AI lead scoring
│   └── utils/
│       ├── stealth.py          # Anti-detection: UA rotation, JS patches, delays
│       └── parsers.py          # Email regex, social link patterns
└── frontend/
    └── src/
        ├── app/
        │   ├── page.tsx        # Main dashboard
        │   ├── layout.tsx      # Root layout
        │   └── globals.css     # Dark design system
        ├── components/
        │   ├── SearchBar.tsx   # Keyword + Location inputs
        │   ├── ResultsTable.tsx # Real-time sortable lead table
        │   ├── ProgressBar.tsx # Phase indicator
        │   ├── ExportButton.tsx # CSV download
        │   └── JobHistory.tsx  # Past jobs sidebar
        └── lib/
            ├── api.ts          # Typed API client
            └── types.ts        # TypeScript interfaces
```

---

## 🔌 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/search` | POST | Start new search job |
| `/api/jobs` | GET | List all jobs |
| `/api/search/{id}` | GET | Job status |
| `/api/search/{id}/leads` | GET | Paginated leads |
| `/api/search/{id}/export` | GET | Download CSV |
| `/api/search/{id}` | DELETE | Delete job |
| `/api/ws/{job_id}` | WebSocket | Real-time updates |

---

## ⚙️ Environment Variables

```env
# backend/.env
DATABASE_URL=sqlite:///./leadscout.db   # or postgres://...
GEMINI_API_KEY=your-key-here           # Get from Google AI Studio
MAX_RESULTS_PER_SEARCH=30
SCRAPE_DELAY_MIN=2.0
SCRAPE_DELAY_MAX=4.0
PORT=8000
```

---

## 🤖 AI Verification

Add your Gemini API key to enable quality scoring:

1. Get a free key at https://aistudio.google.com/
2. Edit `backend/.env` → set `GEMINI_API_KEY=your-key`
3. Restart the backend

Gemini classifies each lead as:
- 🔥 **Hot** — Verified business email, strong domain match
- 🟡 **Warm** — Generic email (info@) or partial match  
- ❄️ **Cold** — No email found or mismatched domain

---

## 🗄️ Switch to PostgreSQL

```bash
# Start Postgres via Docker
docker-compose up -d

# Update backend/.env
DATABASE_URL=postgresql://leadscout:leadscout_secret@localhost:5432/leadscout

# Restart backend
python -m uvicorn main:app --reload --port 8000
```

---

## 📊 Live Test Results

Tested: **"Dentists in Mumbai"**
- ✅ **30 leads** scraped from Google Maps
- 📧 **12 emails** extracted (40% enrichment rate)
- 🔗 Social links (Instagram, Facebook) for multiple businesses
- ⚡ Pipeline: ~2.5 minutes for 30 leads with full AI verification

---

## 🛡️ Anti-Detection

- Human-like typing with randomized delays (40-120ms per character)
- User-agent rotation from a pool of 10+ real Chrome/Firefox/Safari UAs
- Randomized viewport sizes
- Stealth JS patches (masks `navigator.webdriver`, canvas fingerprint noise)
- Media resource blocking for faster loads
- Separate browser context per scrape job
