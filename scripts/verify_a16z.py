"""Verify the generic Firecrawl v2 extractor against a16z.

Default behavior is cache-first: per-category JSON files under ``.firecrawl/``
are loaded if present, and only the missing ones hit the API. Pass
``--refresh`` to force fresh scrapes and overwrite the cache.

On every run, writes a combined ``.firecrawl/a16z.json`` with a ``scraped_at``
timestamp; that file is the deliverable shape downstream consumers should
target.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / ".firecrawl"

load_dotenv(REPO_ROOT / ".env", override=False)

SOURCE_URLS = {
    "team": "https://a16z.com/team/",
    "portfolio": "https://a16z.com/portfolio/",
    "blog": "https://a16z.com/news-content/",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force fresh scrapes; overwrite the cache files.",
    )
    args = parser.parse_args()

    if not os.environ.get("FIRECRAWL_API_KEY"):
        print("Set FIRECRAWL_API_KEY=fc-... in your environment.")
        return 1

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Import lazily so --help works without the SDK installed.
    from pipeline.adapters.web.firecrawl_adapter import FirecrawlWebFetcher
    from pipeline.application.use_cases.vc_firm_extractor import VcFirmExtractor
    from pipeline.frameworks.firecrawl_client import build_firecrawl_client

    extractor = VcFirmExtractor(web=FirecrawlWebFetcher(build_firecrawl_client()))

    team = _load_or_scrape(
        category="team",
        scrape=lambda: extractor.extract_team(SOURCE_URLS["team"]),
        refresh=args.refresh,
    )
    portfolio = _load_or_scrape(
        category="portfolio",
        scrape=lambda: extractor.extract_portfolio(SOURCE_URLS["portfolio"]),
        refresh=args.refresh,
    )
    blog = _load_or_scrape(
        category="blog",
        scrape=lambda: extractor.extract_blog(SOURCE_URLS["blog"]),
        refresh=args.refresh,
    )

    combined = {
        "firm": "a16z",
        "scraped_at": datetime.now(UTC).isoformat(),
        "source_urls": SOURCE_URLS,
        "team": team,
        "portfolio": portfolio,
        "blog": blog,
    }
    combined_path = CACHE_DIR / "a16z.json"
    combined_path.write_text(json.dumps(combined, indent=2), encoding="utf-8")

    _print_summary(team=team, portfolio=portfolio, blog=blog, combined_path=combined_path)
    return 0


def _load_or_scrape(
    *,
    category: str,
    scrape: Callable[[], list[dict[str, Any]]],
    refresh: bool,
) -> list[dict[str, Any]]:
    path = CACHE_DIR / f"a16z_{category}.json"
    if path.exists() and not refresh:
        print(f"[cache] {path.name}")
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, list):
            raise RuntimeError(f"{path}: expected a list, got {type(loaded).__name__}")
        return loaded
    print(f"[fresh] {category} -> {SOURCE_URLS[category]}")
    records = scrape()
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return records


def _print_summary(
    *,
    team: list[dict[str, Any]],
    portfolio: list[dict[str, Any]],
    blog: list[dict[str, Any]],
    combined_path: Path,
) -> None:
    print()
    print("=== a16z verify summary ===")
    print(f"team:      {len(team)} partners")
    print(f"portfolio: {len(portfolio)} companies")
    print(f"blog:      {len(blog)} posts")
    print()

    print("partners:")
    for i, p in enumerate(team, 1):
        print(f"  {i:>2}. {p.get('name') or '(no name)'}")
    print()

    print("companies:")
    for i, c in enumerate(portfolio, 1):
        print(f"  {i:>2}. {c.get('name') or '(no name)'}")
    print()

    team_linkedin = sum(1 for p in team if p.get("linkedin_url"))
    portfolio_linkedin = sum(1 for c in portfolio if c.get("linkedin_url"))
    with_founders = sum(1 for c in portfolio if c.get("founders"))
    team_missing_profile = sum(1 for p in team if not p.get("profile_url"))
    portfolio_missing_detail = sum(1 for c in portfolio if not c.get("detail_url"))

    print(f"team partners with linkedin_url:        {team_linkedin}/{len(team)}")
    print(f"portfolio companies with linkedin_url:  {portfolio_linkedin}/{len(portfolio)}")
    print(f"portfolio companies with founders:      {with_founders}/{len(portfolio)}")
    print(f"team partners missing profile_url:      {team_missing_profile}/{len(team)}")
    print(f"portfolio companies missing detail_url: {portfolio_missing_detail}/{len(portfolio)}")
    print()
    print(f"wrote combined: {combined_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
