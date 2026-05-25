import json
from pathlib import Path

from deal_flow.application.ports.repositories.partner_profile_repository import (
    PartnerProfileRepository,
)
from deal_flow.domain.entities.partner import Partner

# The firm domain in firms.yaml doesn't always match the data file slug.
# (sequoiacap.com → sequoia_partners.json, not sequoiacap_partners.json.)
_DOMAIN_TO_SLUG = {
    "a16z.com": "a16z",
    "sequoiacap.com": "sequoia",
    "ycombinator.com": "ycombinator",
}


def _normalize_photo_url(value: object) -> str | None:
    """a16z's scraped data sometimes returns photo_url as a list of strings
    (Substack subscribe-card fallbacks when og:image is missing). Take the
    first string and treat anything else as missing."""
    if isinstance(value, str):
        return value or None
    if isinstance(value, list) and value:
        first = value[0]
        return first if isinstance(first, str) and first else None
    return None


class FilePartnerProfileRepository(PartnerProfileRepository):
    """Reads ``{data_dir}/{firm_slug}_partners.json``. Unknown firms return
    an empty list rather than erroring — the route layer is the right place
    to decide whether to 404."""

    def __init__(self, data_dir: Path) -> None:
        self._dir = data_dir

    def list_by_firm(self, firm_domain: str) -> list[Partner]:
        slug = _DOMAIN_TO_SLUG.get(firm_domain)
        if not slug:
            return []
        path = self._dir / f"{slug}_partners.json"
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [_to_partner(item) for item in raw.get("partners") or []]


def _to_partner(item: dict) -> Partner:
    return Partner(
        name=item.get("name") or "",
        profile_url=item.get("profile_url") or "",
        role=item.get("role"),
        role_display=item.get("role_display"),
        focus_areas=tuple(item.get("focus_areas") or ()),
        teams=tuple(item.get("teams") or ()),
        bio=item.get("bio"),
        about_short=item.get("about_short"),
        linkedin_url=item.get("linkedin_url"),
        x_url=item.get("x_url"),
        email=item.get("email"),
        photo_url=_normalize_photo_url(item.get("photo_url")),
        education=tuple(item.get("education") or ()),
        prior_experience=tuple(item.get("prior_experience") or ()),
    )
