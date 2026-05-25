"""One-off: scrape Sequoia Capital's portfolio companies (capped at 50).

Sequoia publishes a company sitemap, so listing discovery is free
(no Firecrawl). Detail pages are then batch-scraped to fill in website,
sector, founders, etc.

Output: backend/data/sequoia_portfolio.json
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

PORTFOLIO_URL = "https://sequoiacap.com/our-companies/#all-panel"
SITEMAP_URL = "https://sequoiacap.com/company-sitemap.xml"
LIMIT = 50
OUTPUT_PATH = REPO_BACKEND / "data" / "sequoia_portfolio.json"


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

    print(f"[sequoia] discovering portfolio via sitemap {SITEMAP_URL} …")
    companies = use_case.execute(
        ExtractFirmPortfolioInput(
            portfolio_url=PORTFOLIO_URL,
            limit=LIMIT,
            sitemap_url=SITEMAP_URL,
        )
    )
    print(f"[sequoia] got {len(companies)} companies (cap {LIMIT})")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "firm": "sequoiacap.com",
        "portfolio_url": PORTFOLIO_URL,
        "sitemap_url": SITEMAP_URL,
        "limit": LIMIT,
        "count": len(companies),
        "companies": [asdict(c) for c in companies],
    }, indent=2, ensure_ascii=False))
    print(f"[done] {len(companies)} companies → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
