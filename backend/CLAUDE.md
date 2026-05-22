# Backend — Clean Architecture (Python)

## Layer map

```
domain/          ← Entities (innermost, no deps)
  ↑
application/     ← Use Cases + ports (depends on domain only)
  ↑
interfaces/      ← Controllers, presenters (depends on domain + application)
  ↑                ─── composition root: interfaces/api/dependencies.py ───
infrastructure/  ← Concrete I/O (implements application/ports/*)
```

**The Dependency Rule**: source dependencies point **inward** only. Each layer's `CLAUDE.md` spells out what it may and may not import.

## Where things go

| You're writing… | It belongs in… |
|---|---|
| A business object (`Deal`, `Filing`) | `src/deal_flow/domain/entities/` |
| An immutable value (`Money`, `Cusip`) | `src/deal_flow/domain/value_objects/` |
| A user-facing operation (`FindDeals`, `IngestFiling`) | `src/deal_flow/application/use_cases/` |
| An interface a use case depends on | `src/deal_flow/application/ports/{repositories,services}/` |
| A FastAPI route | `src/deal_flow/interfaces/api/routes/` |
| A Pydantic request/response model | `src/deal_flow/interfaces/api/schemas/` |
| Wiring a port to its concrete adapter | `src/deal_flow/interfaces/api/dependencies.py` |
| A Postgres / S3 / EDGAR client | `src/deal_flow/infrastructure/{persistence,external}/` |
| Env var loading | `src/deal_flow/infrastructure/config/settings.py` |

## Tests
Tests mirror `src/deal_flow/` 1:1. See `tests/CLAUDE.md`.

## Run

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn deal_flow.interfaces.api.app:app --reload
pytest
```
