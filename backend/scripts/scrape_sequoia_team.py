"""One-off: scrape the full Sequoia Capital investment team — no 10-cap.

Reuses FirecrawlExtractor's underlying SDK + FileCache so raw responses land
in backend/.firecrawl/ alongside every other run, but uses a local schema +
prompt that asks for EVERY partner instead of "at most 10".

Output: backend/data/sequoia_partners.json
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

# Sequoia's team page splits the investment team into two tabs (Seed/Early
# and Growth), each rendered as a server-side URL filter. Need both to get
# the full roster — they overlap on a handful of partners who sit on both.
TEAM_URLS = {
    "Seed/Early": "https://sequoiacap.com/our-team/?_role=seed-early",
    "Growth": "https://sequoiacap.com/our-team/?_role=growth",
}
OUTPUT_PATH = REPO_BACKEND / "data" / "sequoia_partners.json"

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
    role: str | None = Field(default=None, description="Job title (e.g. 'Partner'). Return null if not found.")
    profile_url: str | None = Field(
        default=None,
        description="URL to the partner's individual profile page on this site. May be relative.",
    )
    linkedin_url: str | None = Field(default=None, description=_LINKEDIN_HINT)
    x_url: str | None = Field(default=None, description=_X_HINT)


class PartnerListingPageUncapped(BaseModel):
    partners: list[PartnerListing] = Field(
        description=(
            "EVERY investment partner shown on this team page — general partners, "
            "partners, investment partners, growth partners, scout partners, "
            "venture partners. Do not cap the list — include all of them. "
            "EXCLUDE operating staff, recruiters, marketing/comms, EAs, and "
            "non-investing roles."
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
    "Extract EVERY investment partner on this team page. Do not cap or "
    "truncate the list — include every single person whose role is "
    "investment-side (general partner, partner, investment partner, growth, "
    "scout, venture partner, etc.). Include each partner's profile URL "
    "(may be relative) and any LinkedIn/X links visible on the card or in "
    "a social-icon strip. Exclude operating staff, recruiters, marketing, "
    "comms, and EAs."
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

    # 1) Scrape both team tabs and dedupe by profile_url. Track which team(s)
    #    each partner appears under so we can attach that to the output.
    by_profile: dict[str, dict] = {}
    teams_by_profile: dict[str, list[str]] = {}

    for team_name, url in TEAM_URLS.items():
        inputs: dict[str, Any] = {
            "url": url,
            "schema": "PartnerListingPageUncapped",
            "prompt": LISTING_PROMPT,
            "wait_for": 4000,
            "actions": None,
            "proxy": None,
        }
        key = FileCache.key_for("scrape", **inputs)
        hit = cache.read(key)
        if hit is not None:
            payload = hit["payload"]
            print(f"[{team_name}] cache hit — {len(payload.get('partners') or [])} partners")
        else:
            json_format = {
                "type": "json",
                "schema": PartnerListingPageUncapped.model_json_schema(),
                "prompt": LISTING_PROMPT,
            }
            print(f"[{team_name}] scraping {url} …")
            doc = app.scrape(
                url,
                formats=["markdown", json_format],
                actions=[{"type": "wait", "milliseconds": 4000}],
            )
            if not _has_substantive_content(doc):
                print(f"[{team_name}] empty content — skipping", file=sys.stderr)
                continue
            payload = _json_payload(doc)
            cache.write(key, {"op": "scrape", "inputs": inputs,
                              "raw": _to_dict(doc), "payload": payload})
            print(f"[{team_name}] got {len(payload.get('partners') or [])} partners")

        for p in payload.get("partners") or []:
            pu = p.get("profile_url")
            if pu:
                pu = urljoin(url, pu)
                p["profile_url"] = pu
            else:
                continue
            by_profile.setdefault(pu, p)
            teams_by_profile.setdefault(pu, []).append(team_name)

    partners = list(by_profile.values())

    # 2) Batch-scrape profile pages.
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
                    src = _source_url(doc)
                    print(f"[details]   skip empty: {src}")
                    continue
                src = _source_url(doc)
                if src:
                    j = _json_payload(doc)
                    j["photo_url"] = _og_image(doc)
                    details_by_url[src] = j
            cache.write(batch_key, {"op": "batch_scrape", "inputs": batch_inputs,
                                    "raw": raw, "payload": details_by_url})
            print(f"[details] got {len(details_by_url)} profiles")

    # 3) Merge listing + detail. The listing "role" is actually the team tab
    #    (Seed/Early vs Growth) — promote that out of "role" and keep the
    #    detail-page role (which is the actual job title).
    merged: list[dict] = []
    for p in partners:
        pu = p.get("profile_url") or ""
        d = details_by_url.get(pu) or {}
        merged.append({
            "name": p.get("name"),
            "role": d.get("role"),
            "teams": teams_by_profile.get(pu) or [],
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
        "firm": "sequoiacap.com",
        "team_urls": TEAM_URLS,
        "count": len(merged),
        "partners": merged,
    }, indent=2, ensure_ascii=False))
    socials = sum(1 for m in merged if m["linkedin_url"] or m["x_url"])
    print(f"[done] {len(merged)} partners, {socials} with socials → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
