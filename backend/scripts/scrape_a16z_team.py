"""One-off: scrape a16z's full Investing team — no 10-cap.

Different shape from Sequoia/YC: a16z's /team page embeds the entire roster
as a JSON blob in a `data-payload` attribute. Listing extraction is free
(no Firecrawl) — we just parse the embedded JSON and filter by
`role_display` containing "Investing". Firecrawl still does the detail
pass for titles / bios / education / prior experience.

Output: backend/data/a16z_partners.json
"""

from __future__ import annotations

import html as html_lib
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

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

TEAM_URL = "https://a16z.com/team/"
OUTPUT_PATH = REPO_BACKEND / "data" / "a16z_partners.json"

_LINKEDIN_HINT = (
    "Look for a LinkedIn profile link anywhere on the page. Return the full "
    "https://linkedin.com/... URL. Return null if not found."
)
_X_HINT = (
    "Look for an X (formerly Twitter) profile link anywhere on the page. "
    "Return the full https://x.com/... or https://twitter.com/... URL. "
    "Return null if not found."
)


class PartnerDetail(BaseModel):
    role: str | None = Field(default=None, description="Job title on this profile page (e.g. 'General Partner', 'Investing Partner'). Return null if not found.")
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


DETAIL_PROMPT = (
    "This is a single investment partner's profile page. Extract their job "
    "title, full bio text, LinkedIn URL, X/Twitter URL, direct contact email "
    "(if shown), list of schools/degrees, and list of prior companies. "
    "Socials are usually social icons near the name — look carefully. Do "
    "not invent missing fields."
)


def _social(socials: list[dict], substr: str) -> str | None:
    for s in socials or []:
        url = s.get("url") or ""
        if substr in url.lower():
            return url
    return None


def _dedupe_focus_areas(label: str | None) -> list[str]:
    """The page repeats each focus area many times in `focus_areas_label`
    (e.g. 'Growth, Growth, Growth, ...'). Dedupe while preserving order."""
    if not label:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for chunk in (c.strip() for c in label.split(",")):
        if chunk and chunk not in seen:
            seen.add(chunk)
            out.append(chunk)
    return out


def fetch_listing_from_payload() -> list[dict]:
    req = urllib.request.Request(TEAM_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    m = re.search(r'data-payload="([^"]+)"', raw)
    if not m:
        raise SystemExit("a16z /team data-payload not found — page structure changed")
    payload = json.loads(html_lib.unescape(m.group(1)))
    members = payload.get("members") or []
    return [m for m in members if "Investing" in (m.get("role_display") or "")]


def main() -> None:
    settings = get_settings()
    if not settings.firecrawl_api_key:
        print("FIRECRAWL_API_KEY not set", file=sys.stderr)
        sys.exit(2)

    app = Firecrawl(api_key=settings.firecrawl_api_key)
    cache = FileCache(settings.firecrawl_cache_dir)

    investing = fetch_listing_from_payload()
    print(f"[listing] {len(investing)} Investing-role members from /team payload")

    detail_urls = sorted({m["profile_url"] for m in investing if m.get("profile_url")})
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
        hit = cache.read(batch_key)
        if hit is not None:
            details_by_url = hit["payload"]
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

    merged: list[dict] = []
    for m in investing:
        pu = m.get("profile_url") or ""
        d = details_by_url.get(pu) or {}
        socials = m.get("socials") or []
        li = _social(socials, "linkedin.com") or d.get("linkedin_url")
        tw = _social(socials, "twitter.com") or _social(socials, "x.com") or d.get("x_url")
        fc = _social(socials, "farcaster")
        merged.append({
            "name": m.get("name"),
            "role": d.get("role"),
            "role_display": m.get("role_display"),
            "focus_areas": _dedupe_focus_areas(m.get("focus_areas_label")),
            "profile_url": pu,
            "linkedin_url": li,
            "x_url": tw,
            "farcaster_url": fc,
            "email": d.get("email"),
            "photo_url": d.get("photo_url") or m.get("avatar"),
            "bio": d.get("bio"),
            "education": d.get("education") or [],
            "prior_experience": d.get("prior_experience") or [],
        })

    merged.sort(key=lambda x: (x["name"] or "").lower())

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "firm": "a16z.com",
        "team_url": TEAM_URL,
        "count": len(merged),
        "partners": merged,
    }, indent=2, ensure_ascii=False))
    socials_count = sum(1 for x in merged if x["linkedin_url"] or x["x_url"])
    print(f"[done] {len(merged)} partners, {socials_count} with socials → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
