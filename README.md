# deal_flow_finder

Leading-indicator signals for early-stage VC. Discovery, not catch-up.

This repo bootstraps the LAUNCH deal-flow intelligence tool: a five-phase
pipeline that crawls Sequoia / a16z / YC, augments with SEC EDGAR, collects
per-entity activity from X / LinkedIn / partner blogs, then (in the next
workspace) detects signals and writes a daily digest.

See [`PLAN.md`](./PLAN.md) for the full product and architecture write-up.

## Architecture

```
            ┌────────────────────────────────────────────┐
            │                pipeline/main.py            │  ← composition root
            └────────────────────────────────────────────┘
                ▲          ▲           ▲          ▲
                │          │           │          │
       ┌────────┴───┐ ┌────┴─────┐ ┌───┴────┐ ┌───┴────┐
       │ Firecrawl  │ │ EDGAR    │ │ X      │ │ LI     │  adapters/
       └─────┬──────┘ └─────┬────┘ └────┬───┘ └────┬───┘
             └───── implements ports ───┴──────────┘
                              │
                              ▼
            ┌────────────────────────────────────────────┐
            │              pipeline/application/         │  use cases + ports
            └────────────────────────────────────────────┘
                              │
                              ▼
            ┌────────────────────────────────────────────┐
            │             pipeline/entities/            │  Entities + VOs
            └────────────────────────────────────────────┘
```

Dependency rule: arrows point inward only. Swapping any external tool is a
one-adapter, one-line-in-main.py change.

## Running

```bash
# one-time setup
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # fill in API keys

# pipeline
python -m pipeline.main run --phase 1     # crawl Sequoia/a16z/YC → data/firm_graph.json
python -m pipeline.main run --phase 2     # EDGAR Form D pull     → data/filings.json
python -m pipeline.main run --phase 3     # X/LinkedIn/blogs      → data/{social,linkedin,content}/

# api server (serves the sample digest until phase 4 is implemented)
python -m pipeline.main serve             # uvicorn at :8000

# frontend (next.js, reads data/digest.json directly)
cd app && npm install && npm run dev      # http://localhost:3000

# tests + quality gates
pytest                                    # 66+ tests, fakes only — no real APIs
ruff check . && black --check . && mypy pipeline
pre-commit run --all-files                # everything in one shot
```

## Dependencies

### Python (pinned in `pyproject.toml`)

| Package | Version | Purpose |
| --- | --- | --- |
| firecrawl-py | 1.6.4 | Web scraping |
| httpx | 0.27.2 | All non-Firecrawl HTTP |
| anthropic | 0.39.0 | Claude (Phase 4/5) |
| fastapi | 0.115.4 | API server |
| uvicorn | 0.32.0 | FastAPI runtime |
| pydantic | 2.9.2 | Adapter response models (optional use) |
| python-dotenv | 1.0.1 | .env loading |
| pyyaml | 6.0.2 | Config loading |
| typer | 0.12.5 | CLI |

Dev: pytest, pytest-asyncio, respx, mypy, ruff, black, pre-commit.

### Node (under `app/`)
- Next.js 16 (App Router, Tailwind v4, React 19)
- shadcn/ui primitives (Radix / Nova preset)

## Roadmap (v2 and beyond)

- Phase 4 detectors with calibrated scoring (next workspace).
- Phase 5 digest narrative via Claude prompts (next workspace).
- Frontend wired to FastAPI with per-signal drill-down views.
- Snapshot diffing job (cron) so deltas have a stable prior-period.
- Operator watchlist auto-expansion from co-departure clusters.
- Theme-drift visualisation on the digest page.
- SQLite or Postgres swap behind `JsonFileRepository` once data >100MB.
- Authentication + per-user pinning when LAUNCH onboards more partners.

## License

Internal — LAUNCH only.
