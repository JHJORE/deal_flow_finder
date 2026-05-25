"""Verification CLI — exercises the real use cases through the same composition
graph as the API. Stop after each step, inspect output, then move on.

    python -m deal_flow.interfaces.cli.verify_extraction --step 0 --firm a16z.com [--refresh]
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys

from deal_flow.application.use_cases.extract_firm_blog_posts import (
    ExtractFirmBlogPosts,
    ExtractFirmBlogPostsInput,
)
from deal_flow.application.use_cases.extract_firm_partners import (
    ExtractFirmPartners,
    ExtractFirmPartnersInput,
)
from deal_flow.application.use_cases.extract_firm_portfolio import (
    ExtractFirmPortfolio,
    ExtractFirmPortfolioInput,
)
from deal_flow.infrastructure.config.settings import get_settings
from deal_flow.infrastructure.external.firecrawl.extractor import FirecrawlExtractor
from deal_flow.infrastructure.external.firms_registry import FirmSources, load_registry


def _dump(label: str, value) -> None:
    print(f"\n=== {label} ===")
    if dataclasses.is_dataclass(value):
        value = dataclasses.asdict(value)
    elif isinstance(value, list) and value and dataclasses.is_dataclass(value[0]):
        value = [dataclasses.asdict(v) for v in value]
    print(json.dumps(value, indent=2, default=str))


def _resolve(firm: str) -> FirmSources:
    registry = load_registry()
    sources = registry.get(firm)
    if sources is None:
        print(f"firm '{firm}' not in backend/firms.yaml", file=sys.stderr)
        sys.exit(3)
    return sources


def _build_extractor(refresh: bool) -> FirecrawlExtractor:
    settings = get_settings()
    if not settings.firecrawl_api_key:
        print("Set FIRECRAWL_API_KEY=fc-... in your environment.", file=sys.stderr)
        sys.exit(2)
    print(f"[setup] cache: {settings.firecrawl_cache_dir}  refresh: {refresh}")
    return FirecrawlExtractor(
        api_key=settings.firecrawl_api_key,
        cache_dir=settings.firecrawl_cache_dir,
        refresh=refresh,
    )


def step0(firm: str, refresh: bool) -> None:
    """Smoke: load registry, print URLs, scrape the first team URL listing."""
    sources = _resolve(firm)
    _dump(f"firm sources for {firm}", sources)
    if sources.team_payload_url:
        extractor = _build_extractor(refresh)
        listings = extractor.discover_partners_from_payload(
            sources.team_payload_url,
            sources.team_payload_attribute or "data-payload",
            sources.team_payload_role_filter,
        )[:10]
        _dump(f"smoke listing — {len(listings)} partners (payload)", listings)
        return
    if not sources.team_urls:
        print("[step0] firm has no team listing.", file=sys.stderr)
        return
    extractor = _build_extractor(refresh)
    listings = extractor.scrape_partner_listing(sources.team_urls[0])[:10]
    _dump(f"smoke listing — {len(listings)} partners", listings)


def step1(firm: str, refresh: bool) -> None:
    """Partners — listing only (uses every team URL or the payload)."""
    sources = _resolve(firm)
    extractor = _build_extractor(refresh)
    if sources.team_payload_url:
        listings = extractor.discover_partners_from_payload(
            sources.team_payload_url,
            sources.team_payload_attribute or "data-payload",
            sources.team_payload_role_filter,
        )
    elif sources.team_urls:
        listings = [
            item
            for url in sources.team_urls
            for item in extractor.scrape_partner_listing(url)
        ]
    else:
        print("[step1] firm has no team listing.", file=sys.stderr)
        return
    _dump(f"partner listing — {len(listings)}", listings[:20])


def step2(firm: str, refresh: bool) -> None:
    """Partners — full two-stage (listing + detail batch + merge), uncapped."""
    sources = _resolve(firm)
    if not sources.team_urls and not sources.team_payload_url:
        print("[step2] firm has no team listing.", file=sys.stderr)
        return
    extractor = _build_extractor(refresh)
    partners = ExtractFirmPartners(extractor).execute(
        ExtractFirmPartnersInput(
            team_urls=sources.team_urls,
            payload_url=sources.team_payload_url,
            payload_attribute=sources.team_payload_attribute,
            payload_role_filter=sources.team_payload_role_filter,
        )
    )
    socials = sum(1 for p in partners if p.linkedin_url or p.x_url)
    _dump(f"partners — {len(partners)}, {socials} with socials", partners[:20])
    if partners and socials == 0:
        print("\n[FAIL] Batch-wide zero socials — schema/prompt is broken.", file=sys.stderr)
        sys.exit(4)


def step3(firm: str, refresh: bool) -> None:
    """Portfolio — full two-stage."""
    sources = _resolve(firm)
    if not sources.portfolio_url:
        print("[step3] firm has no portfolio_url.", file=sys.stderr)
        return
    extractor = _build_extractor(refresh)
    companies = ExtractFirmPortfolio(extractor).execute(
        ExtractFirmPortfolioInput(
            portfolio_url=sources.portfolio_url,
            sitemap_url=sources.portfolio_sitemap_url,
            html_json_url=sources.portfolio_html_json_url,
            html_json_attribute=sources.portfolio_html_json_attribute,
            limit=10,
        )
    )
    socials = sum(1 for c in companies if c.linkedin_url)
    _dump(f"portfolio — {len(companies)}, {socials} with linkedin", companies)


def step4(firm: str, refresh: bool) -> None:
    """Blog — one-stage."""
    sources = _resolve(firm)
    if not sources.blog_url:
        print("[step4] firm has no blog_url.", file=sys.stderr)
        return
    extractor = _build_extractor(refresh)
    posts = ExtractFirmBlogPosts(extractor).execute(
        ExtractFirmBlogPostsInput(blog_url=sources.blog_url, limit=10)
    )
    _dump(f"blog posts — {len(posts)}", posts)


_STEPS = {0: step0, 1: step1, 2: step2, 3: step3, 4: step4}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--step", type=int, required=True, choices=sorted(_STEPS))
    p.add_argument(
        "--firm",
        default="sequoiacap.com",
        help="firm domain key from backend/firms.yaml (default: sequoiacap.com)",
    )
    p.add_argument("--refresh", action="store_true", help="bypass cache, force fresh API calls")
    args = p.parse_args()
    _STEPS[args.step](args.firm, args.refresh)


if __name__ == "__main__":
    main()
