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

## Test

```bash
cd backend && pytest
```

## Deploy

Push to a Vercel project pointing at this repo. `vercel.json` builds the Next.js app from `frontend/` and exposes the FastAPI app from `api/index.py` under `/api/*`.
