# deal_flow — Clean Architecture

This repo follows **Uncle Bob's Clean Architecture**. The single most important rule:

> **The Dependency Rule:** source code dependencies point *only inward*. Nothing in an inner circle can know anything about something in an outer circle.

```
┌──────────────────────────────────────────────────────────────┐
│  Frameworks & Drivers   (infrastructure/)                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Interface Adapters  (interfaces/)                     │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  Use Cases  (application/)                       │  │  │
│  │  │  ┌────────────────────────────────────────────┐  │  │  │
│  │  │  │  Entities  (domain/)         ← INNERMOST   │  │  │  │
│  │  │  └────────────────────────────────────────────┘  │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
        dependencies point inward  ───►
```

## Repository layout

```
backend/          # Python — Clean Architecture (the 4 layers above)
frontend/        # Next.js — UI only; talks to backend via HTTP
api/             # Vercel Python serverless entrypoint (wraps backend FastAPI)
vercel.json      # Monorepo deploy config
```

## The four layers (what they're for, in one line each)

1. **`backend/src/deal_flow/domain/`** — entities and value objects. Pure business. No I/O, no frameworks.
2. **`backend/src/deal_flow/application/`** — use cases (one per user-facing operation) and the **ports** (ABCs) they depend on.
3. **`backend/src/deal_flow/interfaces/`** — controllers/presenters. Translate HTTP/CLI ↔ use cases. Composition root lives in `interfaces/api/dependencies.py`.
4. **`backend/src/deal_flow/infrastructure/`** — concrete I/O: DB clients, third-party APIs, env loading. Implements the ports defined in `application/`.

Each layer has its own `CLAUDE.md` with allowed/forbidden imports — **read the layer's `CLAUDE.md` before adding code there**.

## How data crosses boundaries

Only **simple data structures** cross layer boundaries — never ORM rows, never framework objects.
- Use cases accept and return DTOs (frozen dataclasses) defined in `application/dtos/`.
- Pydantic models live in `interfaces/api/schemas/` and are converted to/from DTOs at the boundary.

## Frontend ↔ Backend

The frontend never imports from `backend/`. It only calls HTTP routes via `frontend/lib/api/`. In dev, the FastAPI app runs separately; in production, Vercel routes `/api/*` to `api/index.py` which mounts the same FastAPI app.

## Quickstart

```bash
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn deal_flow.interfaces.api.app:app --reload

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

## Further reading
- Uncle Bob, *The Clean Architecture* — https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
