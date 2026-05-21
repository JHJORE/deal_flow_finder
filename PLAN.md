# LAUNCH Deal-Flow Finder — Plan

## Product

LAUNCH is an early-stage VC fund. Its edge is **discovery before consensus**:
acting on a signal before Sequoia, a16z, or YC make their position public.
This tool exists to surface those leading indicators automatically.

The product is a daily digest of the 3-5 strongest signals, each backed by
concrete evidence (a Form D accession, a partner's reply chain, a LinkedIn
title change). Status quo is noise; every metric is a **delta** versus the
prior period.

## Signal Map

The five tiers, in order of conviction:

| Tier | Signal | Detector input |
| --- | --- | --- |
| **1 — deal signals** | `partner_engagement_with_unknown` | likes/replies/quotes graph |
| | `undisclosed_form_d` | EDGAR Form D × firm portfolio |
| | `scout_investment` | EDGAR + scout-fund alias list |
| | `partner_gone_quiet` | post-frequency rolling window |
| | `partner_founder_first_mutual` | following graph deltas |
| **2 — founder heat** | `founder_post_acceleration` | post-frequency delta |
| | `founder_follower_spike` | snapshot delta |
| | `first_senior_linkedin_hire` | LinkedIn company changes |
| **3 — stealth / departure** | `operator_stealth_transition` | LinkedIn title diff |
| | `co_departure_cluster` | LinkedIn current-company deltas |
| | `top_lab_researcher_departure` | watchlist of research orgs |
| **4 — thesis / zeitgeist** | `theme_drift` | tagged post / essay corpora |
| | `partner_essay` | partner blog crawl |
| | `contrarian_partner_stance` | tag co-occurrence outlier |
| | `cross_partner_thesis_alignment` | tag co-occurrence cluster |
| | `engagement_revealed_interest` | likes/replies tagged |
| **5 — discovery** | `new_yc_batch_addition` | portfolio-page diff |
| | `new_portfolio_addition` | portfolio-page diff |
| | `new_partner_at_firm` | people-page diff |

Every entry above maps to a member of `SignalKind` in
`pipeline/entities/value_objects.py`. Adding a tier-N signal requires only a
new `SignalKind` value and a detector — no entity changes.

## Architecture

Clean Architecture with strict inward-pointing dependencies. The test of
correctness is that swapping any external tool — Firecrawl, Anthropic,
twitterapi.io, Proxycurl — is one new adapter file plus one line in
`pipeline/main.py`.

```
              ┌──────────────────────────────────────────┐
              │                  main.py                 │  composition root
              └──────────────────────────────────────────┘
                  │            │             │         │
                  ▼            ▼             ▼         ▼
        ┌─────────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐
        │  adapters   │ │ adapters  │ │ adapters │ │ adapters │
        │  (firecrawl)│ │ (edgar)   │ │ (twitter)│ │ (proxycurl)│
        └──────┬──────┘ └─────┬─────┘ └─────┬────┘ └─────┬────┘
               │              │             │            │
               └────── implements ports ────┴────────────┘
                              ▼
              ┌──────────────────────────────────────────┐
              │              application/                │  use cases + ports
              └──────────────────────────────────────────┘
                              ▼
              ┌──────────────────────────────────────────┐
              │                entities/                 │  Entities + VOs
              └──────────────────────────────────────────┘
```

Layer rules (canonical Clean Architecture names, outermost → innermost):

1. `frameworks/` — **Frameworks & Drivers**. Builds raw external SDK clients
   (Firecrawl, httpx, Anthropic). The only layer that imports those SDKs by
   name. Mostly a handful of `os.environ.get(...) + Client(...)` factories.
2. `adapters/` — **Interface Adapters**. Implements `application/` ports;
   translates between domain types and third-party libraries; catches
   external exceptions and re-raises `DomainError` subclasses. YAML config
   loading lives here too (`adapters/config/`).
3. `application/` — **Use Cases**. One use case per file, all dependencies
   injected via ports (Protocols) in `application/ports/`. Does not know
   that Firecrawl, EDGAR, YAML, or httpx exist.
4. `entities/` — **Entities**. Frozen dataclasses, value objects, domain
   errors. Zero project imports outside the layer; zero external libraries.
5. `main.py` — composition root. The only file that imports across layers.
6. `app/` — Next.js frontend, reads `data/digest.json` directly today and
   the FastAPI server tomorrow.

## Pipeline Phases

| Phase | Output | Status |
| --- | --- | --- |
| 1. Discovery crawl | `data/firm_graph.json` | implemented |
| 2. EDGAR augmentation | `data/filings.json` | implemented |
| 3. Per-entity collection | `data/social/*`, `data/linkedin/*`, `data/content/*` | implemented |
| 4. Tagging + signal detection | `data/signals.json` | **stubbed** |
| 5. Digest generation | `data/digest.json` | **stubbed** (sample shipped) |

## Tool Choices

- **Firecrawl** for web scraping — produces markdown directly, which keeps
  the firm extractors small and parseable. Alternative considered:
  Playwright + a self-hosted reader. Firecrawl wins on time-to-first-data.
- **twitterapi.io** for X data — paid third-party gateway over the Twitter
  API. Avoids the cost and approval delay of the official X API.
- **Proxycurl** for LinkedIn — only sustainable option for LinkedIn data
  short of building a scraper farm. Expensive per call ⇒ cached on disk.
- **EDGAR full-text search** for SEC filings — free, official, well-documented.
- **Anthropic Claude** for all LLM work (tagging, narrative, digest copy) —
  consolidated to one provider for prompt/eval reuse in the next workspace.
- **Python 3.11** + dataclasses for the core domain — type-checks under
  mypy strict without the extra ceremony of pydantic v1.
- **Next.js 15 / 16 App Router** + Tailwind + shadcn/ui — fastest path to a
  data-dense UI that doesn't look generic.

## Out of scope (this workspace)

- Signal detection logic (Phase 4).
- LLM prompts and Claude calls (Phases 4 and 5).
- Frontend beyond the route scaffold (live data wiring is the frontend
  workspace's job).
- Authentication, multi-tenant deployment, scheduled runs — the demo is a
  single-fund, single-operator tool.

## Workspace Plan

Three parallel workspaces. This is the foundation; the other two consume it.

### Signal-detection workspace (next)
Owns: `TagContent`, `DetectSignals`, `GenerateDigest`, `ClaudeAdapter`. Reads
`data/firm_graph.json`, `data/filings.json`, `data/social/*`, `data/linkedin/*`,
`data/content/*`. Writes `data/signals.json` and the real `data/digest.json`.
Adds prompts under `pipeline/prompts/`. Plugs into `main.py` with a new
`--phase 4` / `--phase 5` branch.

### Frontend workspace (parallel)
Owns: replacing the digest/partner/company placeholders with live data from
the FastAPI routes (`/digest`, `/partners/{slug}`, `/companies/{slug}`). Adds
drill-down views: per-signal evidence pages, per-handle timelines. Builds the
"theme drift" visualisation.

### Coordination
- Stable contracts: every entity in `pipeline/entities/models.py` and every
  serialisation helper in `pipeline/main.py` is the API both downstream
  workspaces depend on. Field additions are safe; renames/removes require
  coordination.
- Shared fixtures: `data/firm_graph.json`, `data/filings.json`, and
  `data/digest.json` ship as samples so the downstream workspaces can
  develop offline before real API keys land.
