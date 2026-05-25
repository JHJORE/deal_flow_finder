# deal_flow

Clean Architecture skeleton: **Python backend** + **Next.js frontend**, deployable to Vercel.

## Structure

```
backend/    # Python (FastAPI) — domain / application / interfaces / infrastructure
frontend/   # Next.js 14 App Router (TypeScript, Tailwind)
api/        # Vercel Python serverless entrypoint that mounts the FastAPI app
```

See `CLAUDE.md` for the architecture rules. Each layer has its own `CLAUDE.md`.

## Develop

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn deal_flow.interfaces.api.app:app --reload
```
→ `http://127.0.0.1:8000/health`

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
→ `http://localhost:3000`

## Environment

Copy the example files and fill in keys. The backend reads `backend/.env`; the frontend reads `frontend/.env.local`.

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

**Backend** (`backend/.env`) — all keys are optional; routes that need a missing key return an error at request time.

| Key | Purpose | Where to get it |
|---|---|---|
| `APP_ENV` | `development` or `production` | — |
| `FIRECRAWL_API_KEY` | Scrape firm team pages | https://www.firecrawl.dev/ → Dashboard → API Keys |
| `SEC_USER_AGENT` | Identifies you to SEC EDGAR. Format: `Name email@domain.com` | Required by [SEC fair-access policy](https://www.sec.gov/os/accessing-edgar-data) — no signup |
| `TWITTERAPI_IO_KEY` | Partner X/Twitter activity | https://twitterapi.io/ → Dashboard |
| `APIFY_API_TOKEN` | Partner LinkedIn activity (via `harvestapi~linkedin-profile-posts` actor) | https://console.apify.com/settings/integrations |
| `APIFY_LINKEDIN_ACTOR_ID` | Override the LinkedIn actor (default: `harvestapi~linkedin-profile-posts`) | — |
| `GEMINI_API_KEY` | LLM summarization for `/firms/{domain}/partner-profiles?summarize=true` | https://aistudio.google.com/apikey |
| `DATABASE_URL` | Postgres connection string (reserved; not yet wired) | — |
| `*_CACHE_DIR` / `*_CACHE_REFRESH` | Per-provider on-disk cache location and force-refresh flag | — |
| `PARTNER_DATA_DIR` / `OUTPUT_DIR` / `BACKEND_ROOT` | Path overrides; defaults resolve relative to `backend/` | — |

**Frontend** (`frontend/.env.local`):

| Key | Purpose |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Backend base URL. Defaults to `/api` (Vercel routes it to the Python function). Set to `http://127.0.0.1:8000` for local dev against `uvicorn`. |

## Test

```bash
cd backend && pytest
```

## Deploy

Push to a Vercel project pointing at this repo. `vercel.json` builds the Next.js app from `frontend/` and exposes the FastAPI app from `api/index.py` under `/api/*`.
