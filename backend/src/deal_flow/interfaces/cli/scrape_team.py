"""Scrape a firm's full investment team and write the result to a JSON file.

Drives the same ``ExtractFirmPartners`` use case the API does — picks the
right listing strategy (multi-URL Firecrawl, or HTML-embedded payload)
from the firm's ``firms.yaml`` entry.

    python -m deal_flow.interfaces.cli.scrape_team --firm sequoiacap.com
    python -m deal_flow.interfaces.cli.scrape_team --firm a16z.com --limit 25
    python -m deal_flow.interfaces.cli.scrape_team --firm ycombinator.com --refresh

Output: ``backend/data/<firm>_partners.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from deal_flow.application.use_cases.extract_firm_partners import (
    ExtractFirmPartners,
    ExtractFirmPartnersInput,
)
from deal_flow.infrastructure.config.settings import get_settings
from deal_flow.infrastructure.external.firecrawl.extractor import FirecrawlExtractor
from deal_flow.infrastructure.external.firms_registry import load_registry

_BACKEND_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_OUT_DIR = _BACKEND_ROOT / "data"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--firm", required=True, help="firm domain key from backend/firms.yaml")
    p.add_argument("--limit", type=int, default=None, help="cap partners (default: no cap)")
    p.add_argument("--refresh", action="store_true", help="bypass Firecrawl cache")
    p.add_argument("--output", type=Path, default=None, help="output JSON path")
    args = p.parse_args()

    registry = load_registry()
    sources = registry.get(args.firm)
    if sources is None:
        print(f"firm '{args.firm}' not in backend/firms.yaml", file=sys.stderr)
        sys.exit(3)
    if not sources.team_urls and not sources.team_payload_url:
        print(f"firm '{args.firm}' has no team listing in firms.yaml", file=sys.stderr)
        sys.exit(3)

    settings = get_settings()
    if not settings.firecrawl_api_key:
        print("Set FIRECRAWL_API_KEY=fc-... in your environment.", file=sys.stderr)
        sys.exit(2)

    extractor = FirecrawlExtractor(
        api_key=settings.firecrawl_api_key,
        cache_dir=settings.firecrawl_cache_dir,
        refresh=args.refresh,
    )
    print(f"[setup] firm={args.firm} limit={args.limit} cache={settings.firecrawl_cache_dir} "
          f"refresh={args.refresh}")
    if sources.team_payload_url:
        print(f"[strategy] payload: {sources.team_payload_url} "
              f"attr={sources.team_payload_attribute} filter={sources.team_payload_role_filter!r}")
    else:
        print(f"[strategy] firecrawl: {list(sources.team_urls)}")

    partners = ExtractFirmPartners(extractor).execute(
        ExtractFirmPartnersInput(
            team_urls=sources.team_urls,
            payload_url=sources.team_payload_url,
            payload_attribute=sources.team_payload_attribute,
            payload_role_filter=sources.team_payload_role_filter,
            limit=args.limit,
        )
    )

    out_path = args.output or (_DEFAULT_OUT_DIR / f"{args.firm}_partners.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "firm": args.firm,
                "team_urls": list(sources.team_urls) or None,
                "team_payload_url": sources.team_payload_url,
                "count": len(partners),
                "partners": [asdict(p) for p in partners],
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )
    socials = sum(1 for p in partners if p.linkedin_url or p.x_url)
    print(f"[done] {len(partners)} partners, {socials} with socials → {out_path}")


if __name__ == "__main__":
    main()
