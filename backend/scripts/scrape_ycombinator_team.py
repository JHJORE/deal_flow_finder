"""One-off: scrape YC's group partners — no 10-cap.

Same pattern as scrape_sequoia_team.py. YC has a single /partners page
(no Seed/Early vs Growth tabs), so this is simpler — one listing scrape,
then a batch over each /people/<slug> profile.

Output: backend/data/ycombinator_partners.json
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
    _og_image,
    _source_url,
    _to_dict,
)

TEAM_URL = "https://www.ycombinator.com/partners"
OUTPUT_PATH = REPO_BACKEND / "data" / "ycombinator_partners.json"

_LINKEDIN_HINT = (
    "Look for a LinkedIn profile link anywhere on the page — header, bio, "
    "footer, social icons. Return the full https://linkedin.com/... URL. "
    "Return null if not found."
)
_X_HINT = (
    "Look for an X (formerly Twitter) profile link anywhere on the page — "
    "header, bio, footer, social icons (the icon may be labeled X or Twitter). "
    "Return the full https://x.com/... or https://twitter.com/... URL. "
    "Return null if not found."
)


class PartnerListing(BaseModel):
    name: str = Field(description="Full name of the investment partner.")
    role: str | None = Field(default=None, description="Job title (e.g. 'Group Partner'). Return null if not found.")
    profile_url: str | None = Field(
        default=None,
        description="URL to the partner's individual profile page on this site. May be relative.",
    )
    linkedin_url: str | None = Field(default=None, description=_LINKEDIN_HINT)
    x_url: str | None = Field(default=None, description=_X_HINT)


class PartnerListingPageUncapped(BaseModel):
    partners: list[PartnerListing] = Field(
        description=(
            "EVERY investment partner / group partner shown on this team page. "
            "Do not cap the list — include all of them. EXCLUDE operating "
            "staff, recruiters, marketing/comms, EAs, and non-investing roles."
        )
    )


class PartnerDetail(BaseModel):
    role: str | None = Field(default=None, description="Job title on this profile page. Return null if not found.")
    bio: str | None = Field(default=None, description="Full biography text. Return null if not present.")
    linkedin_url: str | None = Field(default=None, description=_LINKEDIN_HINT)
    x_url: str | None = Field(default=None, description=_X_HINT)
    email: str | None = Field(
        default=None,
        description=(
            "Direct contact email if shown — bio text, contact section, near "
            "social icons. Accept obfuscated forms ('name [at] firm.com'). "
            "Return null if not shown."
        ),
    )
    education: list[str] = Field(default_factory=list, description="Schools / degrees, verbatim.")
    prior_experience: list[str] = Field(default_factory=list, description="Prior companies / roles, verbatim.")


LISTING_PROMPT = (
    "Extract EVERY investment partner / group partner on this page. Do not "
    "cap or truncate the list — include every single person whose role is "
    "investment-side. Include each partner's profile URL (may be relative) "
    "and any LinkedIn/X links visible on the card. Exclude operating staff, "
    "recruiters, marketing, comms, and EAs."
)

DETAIL_PROMPT = (
    "This is a single investment partner's profile page. Extract their job "
    "title, full bio text, LinkedIn URL, X/Twitter URL, direct contact email "
    "(if shown), list of schools/degrees, and list of prior companies. "
    "Socials are usually social icons near the name — look carefully. Do "
    "not invent missing fields."
)


def main() -> None:
    settings = get_settings()
    if not settings.firecrawl_api_key:
        print("FIRECRAWL_API_KEY not set", file=sys.stderr)
        sys.exit(2)

    app = Firecrawl(api_key=settings.firecrawl_api_key)
    cache = FileCache(settings.firecrawl_cache_dir)

    # 1) Listing
    listing_inputs: dict[str, Any] = {
        "url": TEAM_URL,
        "schema": "PartnerListingPageUncapped",
        "prompt": LISTING_PROMPT,
        "wait_for": 4000,
        "actions": None,
        "proxy": None,
    }
    listing_key = FileCache.key_for("scrape", **listing_inputs)
    hit = cache.read(listing_key)
    if hit is not None:
        listing_payload = hit["payload"]
        print(f"[listing] cache hit — {len(listing_payload.get('partners') or [])} partners")
    else:
        json_format = {
            "type": "json",
            "schema": PartnerListingPageUncapped.model_json_schema(),
            "prompt": LISTING_PROMPT,
        }
        print(f"[listing] scraping {TEAM_URL} …")
        doc = app.scrape(
            TEAM_URL,
            formats=["markdown", json_format],
            actions=[{"type": "wait", "milliseconds": 4000}],
        )
        if not _has_substantive_content(doc):
            print("[listing] empty content — aborting", file=sys.stderr)
            sys.exit(3)
        listing_payload = _json_payload(doc)
        cache.write(listing_key, {"op": "scrape", "inputs": listing_inputs,
                                  "raw": _to_dict(doc), "payload": listing_payload})
        print(f"[listing] got {len(listing_payload.get('partners') or [])} partners")

    partners = listing_payload.get("partners") or []
    seen: set[str] = set()
    deduped: list[dict] = []
    for p in partners:
        pu = p.get("profile_url")
        if pu:
            p["profile_url"] = urljoin(TEAM_URL, pu)
        key = p["profile_url"] or (p.get("name") or "").strip().lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)
    partners = deduped

    # 2) Batch detail
    detail_urls = sorted({p["profile_url"] for p in partners if p.get("profile_url")})
    details_by_url: dict[str, dict] = {}
    if detail_urls:
        batch_inputs: dict[str, Any] = {
            "urls": detail_urls,
            "schema": "PartnerDetail",
            "prompt": DETAIL_PROMPT,
            "wait_for": None,
            "actions": None,
            "proxy": None,
        }
        batch_key = FileCache.key_for("batch_scrape", **batch_inputs)
        batch_hit = cache.read(batch_key)
        if batch_hit is not None:
            details_by_url = batch_hit["payload"]
            print(f"[details] cache hit — {len(details_by_url)} profiles")
        else:
            json_format = {
                "type": "json",
                "schema": PartnerDetail.model_json_schema(),
                "prompt": DETAIL_PROMPT,
            }
            print(f"[details] batch scraping {len(detail_urls)} profiles …")
            result = app.batch_scrape(detail_urls, formats=["markdown", json_format])
            raw = _to_dict(result)
            for doc in raw.get("data") or []:
                if not _has_substantive_content(doc):
                    print(f"[details]   skip empty: {_source_url(doc)}")
                    continue
                src = _source_url(doc)
                if src:
                    j = _json_payload(doc)
                    j["photo_url"] = _og_image(doc)
                    details_by_url[src] = j
            cache.write(batch_key, {"op": "batch_scrape", "inputs": batch_inputs,
                                    "raw": raw, "payload": details_by_url})
            print(f"[details] got {len(details_by_url)} profiles")

    # 3) Merge
    merged: list[dict] = []
    for p in partners:
        pu = p.get("profile_url") or ""
        d = details_by_url.get(pu) or {}
        merged.append({
            "name": p.get("name"),
            "role": d.get("role") or p.get("role"),
            "profile_url": pu,
            "linkedin_url": d.get("linkedin_url") or p.get("linkedin_url"),
            "x_url": d.get("x_url") or p.get("x_url"),
            "email": d.get("email"),
            "photo_url": d.get("photo_url"),
            "bio": d.get("bio"),
            "education": d.get("education") or [],
            "prior_experience": d.get("prior_experience") or [],
        })

    merged.sort(key=lambda x: (x["name"] or "").lower())

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "firm": "ycombinator.com",
        "team_url": TEAM_URL,
        "count": len(merged),
        "partners": merged,
    }, indent=2, ensure_ascii=False))
    socials = sum(1 for m in merged if m["linkedin_url"] or m["x_url"])
    print(f"[done] {len(merged)} partners, {socials} with socials → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
