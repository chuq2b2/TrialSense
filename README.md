<img width="500" height="auto" alt="logo" src="https://github.com/user-attachments/assets/59c13c22-a12c-4d8d-a282-d24e0fc75909" />

Live DEMO: https://trial-sense.vercel.app/

# TrialSense

TrialSense helps clinical trial coordinators find and rank eligible patients for a study. Enter an NCT ID or ClinicalTrials.gov URL, and the app fetches trial eligibility, scores synthetic patients against inclusion/exclusion criteria, and returns a ranked list with match details and PCP contact information.

Built for coordinators with appropriate patient data clearance. Patient identifiers and clinical details are shown in match results.

---

## Problem

Clinical trial patient recruitment remains largely manual. Coordinators must review health records, interpret complex inclusion/exclusion criteria, and route candidates for human review and consent.

Around 80% of trials fail to meet initial enrollment targets on time. Delays can cost drug developers up to **$8M per day** in lost revenue.

## Solution

TrialSense automates the first pass of trial–patient matching:

1. **Fetch** a trial from [ClinicalTrials.gov](https://clinicaltrials.gov)
2. **Parse** eligibility into structured rules
3. **Pre-filter** patients with SQL hard rules (age, sex, conditions)
4. **Score** each patient with a rule-based engine
5. **Present** ranked matches with inclusion/exclusion breakdowns and PCP contacts

Patient data comes from the public [Synthea](https://synthea.mitre.org/) synthetic dataset (~111 patients). Trial data comes from the ClinicalTrials.gov API.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, Vite, Tailwind CSS v4, shadcn/ui (Radix) |
| **Backend** | FastAPI, Uvicorn, Pydantic v2 |
| **Database** | SQLite (default) or PostgreSQL (optional) |
| **Patient data** | Synthea CSVs → seeded SQLite/Postgres |
| **Trial data** | ClinicalTrials.gov API v2 |
| **Optional LLM** | Nebius Token Factory (OpenAI-compatible API) |

---

## How It Works

```
User enters NCT ID / CT.gov URL
        ↓
POST /api/trials/lookup  →  ClinicalTrials.gov
        ↓
Trial summary (title, conditions, eligibility text)
        ↓
POST /api/trials/match
        ↓
┌─────────────────────────────────────────┐
│  1. Criteria extraction (criteria.py)   │
│     Parse inclusion/exclusion lines     │
│     into structured rules + match_terms │
├─────────────────────────────────────────┤
│  2. SQL pre-filter (database.py)        │
│     Age, sex, condition overlap         │
├─────────────────────────────────────────┤
│  3. Heuristic scoring (scoring.py)      │
│     Per-criterion 1 / 0 / 0.5 / U       │
│     Match %, bands, inclusion/exclusion │
│     summaries                           │
└─────────────────────────────────────────┘
        ↓
Ranked patient matches → React UI (paginated)
```

### Scoring engine (default)

TrialSense uses an **in-house, rule-based eligibility engine** — not an LLM by default:

- **Local parsing** — splits eligibility text into individual inclusion/exclusion criteria
- **SQL pre-filter** — hard rules (age range, sex, required/excluded conditions)
- **Heuristic scorer** — checks patient fields (age, sex, conditions, medications, vitals)
- **Match %** — weighted inclusion score with verification penalty; hard exclusions block at 0%
- **Summaries** — per-criterion status (met / unmet / unverified for inclusion; cleared / triggered / unverified for exclusion)

Many trial-specific fields (HER2, ECOG, PCL-5, tumor size, etc.) are **unverified** when Synthea data lacks them — match scores reflect that honestly.

### Optional Nebius LLM

LLM integration exists but is **disabled by default** for speed (~sub-second vs minutes).

Enable in `backend/.env.local`:

```env
USE_LLM_CRITERIA=true
USE_LLM_SCORING=true
NEBIUS_API_KEY=your_key_here
```

| Flag | Effect |
|------|--------|
| `USE_LLM_CRITERIA` | Nebius structures eligibility (fallback: local parser) |
| `USE_LLM_SCORING` | Nebius scores patients (fallback: heuristics) |

---

## Project Structure

```
TrialSense/
├── backend/
│   ├── main.py              # FastAPI routes
│   ├── matching.py          # Pipeline orchestration
│   ├── criteria.py          # Eligibility → structured rules
│   ├── scoring.py           # Heuristic + optional LLM scoring
│   ├── database.py          # SQL pre-filter
│   ├── patients.py          # Synthea CSV loader
│   ├── condition_matching.py
│   ├── ctgov.py             # ClinicalTrials.gov client
│   ├── nebius_client.py     # Optional LLM client
│   ├── seed_db.py             # CSV → database
│   └── schemas.py           # Pydantic API models
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── api/trials.js
│       └── components/
│           ├── TrialInputForm.jsx
│           ├── TrialResult.jsx
│           └── MatchResults.jsx
├── data/synthea/            # Patient CSVs
├── main.py                  # Uvicorn entrypoint (repo root)
└── docker-compose.yml       # Optional PostgreSQL
```

---

## Run Locally

### Prerequisites

- Python 3.11+
- Node.js 18+

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python3 seed_db.py
uvicorn main:app --reload --port 8000
```

Or from the repo root:

```bash
pip install -r backend/requirements.txt
cd backend && python3 seed_db.py && cd ..
uvicorn main:app --reload --port 8000
```

Re-run `python3 seed_db.py` after schema changes.

API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Vite proxies `/api` to the backend on port 8000.

### 3. Environment (optional)

Copy `backend/.env.example` to `backend/.env.local`:

```env
DB_BACKEND=sqlite
NEBIUS_API_KEY=your_nebius_api_key_here
USE_LLM_CRITERIA=false
USE_LLM_SCORING=false
```

### 4. PostgreSQL (optional)

```bash
docker compose up -d
```

Set in `backend/.env.local`:

```env
DB_BACKEND=postgresql
DATABASE_URL=postgresql://trialsense:trialsense@localhost:5432/trialsense
```

Then seed: `python3 seed_db.py`

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/trials/lookup` | Fetch trial by NCT ID or CT.gov URL |
| `POST` | `/api/trials/match` | Score patients against trial eligibility |

---

## Match Results UI

Each match card shows:

- **Header** — rank, match %, band, patient ID, age, sex, location, care site
- **Actions** — View details (inclusion + exclusion criteria), Contact PCP
- **Collapsible** — full patient name, vitals, conditions, medications
- **Pagination** — 5 matches per page

---

## Data Sources

- **Patients:** Synthea synthetic EHR (`data/synthea/patient_master.csv`, `patient_provider.csv`, `providers_clean.csv`)
- **Trials:** [ClinicalTrials.gov API v2](https://clinicaltrials.gov/data-api/api)

---

## Deploy on Vercel

TrialSense deploys as a **single Vercel project**: Vite frontend (static) + FastAPI backend (Python serverless function).

### Prerequisites

- [Vercel account](https://vercel.com)
- [Vercel CLI](https://vercel.com/docs/cli) (optional): `npm i -g vercel`

### Deploy

1. Push the repo to GitHub (if not already).

2. Import the project in [Vercel Dashboard](https://vercel.com/new):
   - **Root directory:** repository root (not `frontend/`)
   - Vercel reads `vercel.json` automatically.

3. Or deploy from the CLI:

```bash
cd /path/to/TrialSense
vercel
```

4. For production:

```bash
vercel --prod
```

### What happens on deploy

- Installs frontend + Python dependencies
- Runs `python backend/seed_db.py` (builds SQLite from Synthea CSVs)
- Builds `frontend/dist`
- Serves the React app and routes `/api/*` to `api/index.py` (FastAPI)

### Environment variables (Vercel project settings)

Optional — only if you enable LLM scoring:

| Variable | Value |
|----------|-------|
| `USE_LLM_CRITERIA` | `true` |
| `USE_LLM_SCORING` | `true` |
| `NEBIUS_API_KEY` | your key |
| `NEBIUS_BASE_URL` | `https://api.tokenfactory.nebius.com/v1` |

For PostgreSQL instead of SQLite, set `DB_BACKEND=postgresql` and `DATABASE_URL` (e.g. Neon, Supabase, or Vercel Postgres).

### Notes

- **Same-origin API:** Production uses `/api` relative URLs — no separate backend URL needed.
- **Serverless timeout:** Hobby plan = 10s per request; Pro allows up to 60s (`maxDuration` in `vercel.json`).
- **SQLite:** Re-seeded on each deploy; patient data is read-only at runtime.
- **Local dev** is unchanged — run backend + `npm run dev` separately.

---

## License

See repository for license details.
