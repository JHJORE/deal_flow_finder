"""One-off: scrape a16z's portfolio companies (capped at 50).

a16z embeds the full company list as JSON in a `data-companies` attribute
on /portfolio, so listing discovery is free (no Firecrawl) and rich enough
that the use case skips the detail batch entirely.

Output: backend/data/a16z_portfolio.json
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_BACKEND / "src"))

from deal_flow.application.use_cases.extract_firm_portfolio import (  # noqa: E402
    ExtractFirmPortfolio,
    ExtractFirmPortfolioInput,
)
from deal_flow.infrastructure.config.settings import get_settings  # noqa: E402
from deal_flow.infrastructure.external.firecrawl.extractor import (  # noqa: E402
    FirecrawlExtractor,
)

PORTFOLIO_URL = "https://a16z.com/portfolio/"
HTML_JSON_URL = "https://a16z.com/portfolio/"
HTML_JSON_ATTR = "data-companies"
LIMIT = 50
OUTPUT_PATH = REPO_BACKEND / "data" / "a16z_portfolio.json"


def main() -> None:
    settings = get_settings()
    if not settings.firecrawl_api_key:
        print("FIRECRAWL_API_KEY not set", file=sys.stderr)
        sys.exit(2)

    extractor = FirecrawlExtractor(
        api_key=settings.firecrawl_api_key,
        cache_dir=settings.firecrawl_cache_dir,
        refresh=settings.firecrawl_cache_refresh,
    )
    use_case = ExtractFirmPortfolio(extractor=extractor)

    print(f"[a16z] discovering portfolio via {HTML_JSON_ATTR} on {HTML_JSON_URL} …")
    companies = use_case.execute(
        ExtractFirmPortfolioInput(
            portfolio_url=PORTFOLIO_URL,
            limit=LIMIT,
            html_json_url=HTML_JSON_URL,
            html_json_attribute=HTML_JSON_ATTR,
        )
    )
    print(f"[a16z] got {len(companies)} companies (cap {LIMIT})")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "firm": "a16z.com",
        "portfolio_url": PORTFOLIO_URL,
        "html_json_url": HTML_JSON_URL,
        "html_json_attribute": HTML_JSON_ATTR,
        "limit": LIMIT,
        "count": len(companies),
        "companies": [asdict(c) for c in companies],
    }, indent=2, ensure_ascii=False))
    print(f"[done] {len(companies)} companies → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
