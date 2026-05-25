import json
from pathlib import Path

from deal_flow.application.ports.repositories.partner_directory import (
    PartnerDirectory,
)
from deal_flow.domain.entities.partner import Partner

# Firm-domain → fixture filename stem in ``backend/data/``. Map explicitly so
# we don't silently 404 on a typo'd domain or accidentally read a file from
# a similarly-named firm.
_FIRM_FILE_MAP = {
    "a16z.com": "a16z_partners",
    "sequoiacap.com": "sequoia_partners",
    "ycombinator.com": "ycombinator_partners",
}


class FilePartnerDirectory(PartnerDirectory):
    """``PartnerDirectory`` backed by the pre-scraped JSON fixtures in
    ``backend/data/{firm}_partners.json``.

    Those fixtures are produced by the one-off scripts under
    ``backend/scripts/`` and capture the partner roster (with LinkedIn / X
    URLs) at a point in time. This adapter is the read-side of that data.
    """

    def __init__(self, data_dir: Path) -> None:
        self._dir = data_dir

    def list_partners(self, firm_domain: str) -> list[Partner]:
        stem = _FIRM_FILE_MAP.get(firm_domain)
        if stem is None:
            raise FileNotFoundError(
                f"no partner fixture configured for firm '{firm_domain}'"
            )
        path = self._dir / f"{stem}.json"
        if not path.exists():
            raise FileNotFoundError(f"partner fixture not found: {path}")
        raw = json.loads(path.read_text(encoding="utf-8"))
        entries = raw.get("partners") if isinstance(raw, dict) else raw
        if not isinstance(entries, list):
            return []
        return [_to_partner(e) for e in entries if isinstance(e, dict)]


def _to_partner(raw: dict) -> Partner:
    return Partner(
        name=str(raw.get("name") or ""),
        profile_url=str(raw.get("profile_url") or ""),
        role=_str(raw.get("role")),
        bio=_str(raw.get("bio")),
        linkedin_url=_str(raw.get("linkedin_url")),
        x_url=_str(raw.get("x_url")),
        email=_str(raw.get("email")),
        photo_url=_str(raw.get("photo_url")),
        education=tuple(_str_list(raw.get("education"))),
        prior_experience=tuple(_str_list(raw.get("prior_experience"))),
    )


def _str(value: object) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v) for v in value if v not in (None, "")]
