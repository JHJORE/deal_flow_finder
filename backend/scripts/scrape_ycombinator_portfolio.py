"""One-off: scrape Y Combinator's portfolio companies (capped at 50).

YC's /companies page has no embedded JSON or sitemap we can exploit for
free, so listing discovery falls through to an LLM-driven Firecrawl scrape.
The shared PortfolioListingPage schema is hardcoded to "Return at most 10",
so this script defines its own uncapped schema (mirroring how
scrape_ycombinator_team.py escapes the same 10-cap on partners) and calls
Firecrawl directly. We then take the first LIMIT companies and batch-scrape
their detail pages with the shared PORTFOLIO_DETAIL_PROMPT.

Output: backend/data/ycombinator_portfolio.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from firecrawl import Firecrawl
from pydantic import BaseModel, Field

REPO_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_BACKEND / "src"))

from deal_flow.infrastructure.cache.file_cache import FileCache  # noqa: E402
from deal_flow.infrastructure.config.settings import get_settings  # noqa: E402
from deal_flow.infrastructure.external.firecrawl.extractor import (  # noqa: E402
    _has_substantive_content,
    _json_payload,
    _source_url,
    _to_dict,
)
from deal_flow.infrastructure.external.firecrawl.schemas import (  # noqa: E402
    PORTFOLIO_DETAIL_PROMPT,
    PortfolioDetail,
)

PORTFOLIO_URL = "https://www.ycombinator.com/companies"
LIMIT = 50
OUTPUT_PATH = REPO_BACKEND / "data" / "ycombinator_portfolio.json"


class _Listing(BaseModel):
    name: str = Field(description="Company name on the portfolio listing card.")
    detail_url: str | None = Field(
        default=None,
        description=(
            "URL to the company's detail page on this site. May be relative. "
            "Return null if the card has no detail link."
        ),
    )
    website: str | None = Field(
        default=None,
        description="External company website if shown on the card. Return null if not shown.",
    )
    sector: str | None = Field(
        default=None,
        description="Sector/category tag on the card (e.g. 'AI'). Return null if not shown.",
    )


class PortfolioListingUncapped(BaseModel):
    companies: list[_Listing] = Field(
        description=(
            "EVERY portfolio company shown on this listing page. Do not cap "
            "or truncate the list — include every company card visible."
        )
    )


LISTING_PROMPT = (
    "Extract EVERY portfolio company on this page with name, detail URL "
    "(may be relative), external website if shown, and sector/category tag "
    "if shown. Do not cap or truncate the list — include every company "
    "card visible."
)


def main() -> None:
    settings = get_settings()
    if not settings.firecrawl_api_key:
        print("FIRECRAWL_API_KEY not set", file=sys.stderr)
        sys.exit(2)

    app = Firecrawl(api_key=settings.firecrawl_api_key)
    cache = FileCache(settings.firecrawl_cache_dir)

    # 1) Listing — uncapped LLM scrape.
    listing_inputs: dict[str, Any] = {
        "url": PORTFOLIO_URL,
        "schema": "PortfolioListingUncapped",
        "prompt": LISTING_PROMPT,
        "wait_for": 4000,
        "actions": None,
        "proxy": None,
    }
    listing_key = FileCache.key_for("scrape", **listing_inputs)
    hit = cache.read(listing_key)
    if hit is not None:
        listing_payload = hit["payload"]
        print(f"[listing] cache hit — {len(listing_payload.get('companies') or [])} companies")
    else:
        json_format = {
            "type": "json",
            "schema": PortfolioListingUncapped.model_json_schema(),
            "prompt": LISTING_PROMPT,
        }
        print(f"[listing] scraping {PORTFOLIO_URL} …")
        doc = app.scrape(
            PORTFOLIO_URL,
            formats=["markdown", json_format],
            actions=[{"type": "wait", "milliseconds": 4000}],
        )
        if not _has_substantive_content(doc):
            print("[listing] empty content — aborting", file=sys.stderr)
            sys.exit(3)
        listing_payload = _json_payload(doc)
        cache.write(listing_key, {"op": "scrape", "inputs": listing_inputs,
                                  "raw": _to_dict(doc), "payload": listing_payload})
        print(f"[listing] got {len(listing_payload.get('companies') or [])} companies")

    companies = listing_payload.get("companies") or []

    # Normalize relative URLs, dedupe by detail_url (fall back to name).
    seen: set[str] = set()
    deduped: list[dict] = []
    for c in companies:
        du = c.get("detail_url")
        if du:
            c["detail_url"] = urljoin(PORTFOLIO_URL, du)
        key = c.get("detail_url") or (c.get("name") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(c)
    companies = deduped[:LIMIT]
    print(f"[listing] taking first {len(companies)} (cap {LIMIT})")

    # 2) Detail batch.
    detail_urls = sorted({c["detail_url"] for c in companies if c.get("detail_url")})
    details_by_url: dict[str, dict] = {}
    if detail_urls:
        batch_inputs: dict[str, Any] = {
            "urls": detail_urls,
            "schema": "PortfolioDetail",
            "prompt": PORTFOLIO_DETAIL_PROMPT,
            "wait_for": None,
            "actions": None,
            "proxy": None,
        }
        batch_key = FileCache.key_for("batch_scrape", **batch_inputs)
        batch_hit = cache.read(batch_key)
        if batch_hit is not None:
            details_by_url = batch_hit["payload"]
            print(f"[details] cache hit — {len(details_by_url)} pages")
        else:
            json_format = {
                "type": "json",
                "schema": PortfolioDetail.model_json_schema(),
                "prompt": PORTFOLIO_DETAIL_PROMPT,
            }
            print(f"[details] batch scraping {len(detail_urls)} pages …")
            result = app.batch_scrape(detail_urls, formats=["markdown", json_format])
            raw = _to_dict(result)
            for doc in raw.get("data") or []:
                if not _has_substantive_content(doc):
                    print(f"[details]   skip empty: {_source_url(doc)}")
                    continue
                src = _source_url(doc)
                if src:
                    details_by_url[src] = _json_payload(doc)
            cache.write(batch_key, {"op": "batch_scrape", "inputs": batch_inputs,
                                    "raw": raw, "payload": details_by_url})
            print(f"[details] got {len(details_by_url)} pages")

    # 3) Merge listing + detail.
    merged: list[dict] = []
    for c in companies:
        du = c.get("detail_url") or ""
        d = details_by_url.get(du) or {}
        merged.append({
            "name": c.get("name"),
            "detail_url": du,
            "website": d.get("website") or c.get("website"),
            "sector": d.get("sector") or c.get("sector"),
            "description": d.get("description"),
            "linkedin_url": d.get("linkedin_url"),
            "photo_url": None,
            "founders": [
                {"name": f.get("name"), "role": f.get("role")}
                for f in (d.get("founders") or [])
                if f and f.get("name")
            ],
        })

    merged.sort(key=lambda x: (x["name"] or "").lower())

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "firm": "ycombinator.com",
        "portfolio_url": PORTFOLIO_URL,
        "limit": LIMIT,
        "count": len(merged),
        "companies": merged,
    }, indent=2, ensure_ascii=False))
    print(f"[done] {len(merged)} companies → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
