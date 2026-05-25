import json
from pathlib import Path

from deal_flow.application.ports.repositories.portfolio_company_repository import (
    PortfolioCompanyRepository,
)
from deal_flow.domain.entities.founder import Founder
from deal_flow.domain.entities.portfolio_company import PortfolioCompany

# Same domain-to-slug map used by the partner-profiles adapter — the
# portfolio JSON files sit alongside the partner ones in backend/data/.
_DOMAIN_TO_SLUG = {
    "a16z.com": "a16z",
    "sequoiacap.com": "sequoia",
    "ycombinator.com": "ycombinator",
}


class FilePortfolioCompanyRepository(PortfolioCompanyRepository):
    """Reads ``{data_dir}/{firm_slug}_portfolio.json``. Unknown firms return
    an empty list rather than erroring — the route layer is the right place
    to decide whether to 404."""

    def __init__(self, data_dir: Path) -> None:
        self._dir = data_dir

    def list_by_firm(self, firm_domain: str) -> list[PortfolioCompany]:
        slug = _DOMAIN_TO_SLUG.get(firm_domain)
        if not slug:
            return []
        path = self._dir / f"{slug}_portfolio.json"
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [_to_company(item) for item in raw.get("companies") or []]


def _to_company(item: dict) -> PortfolioCompany:
    return PortfolioCompany(
        name=item.get("name") or "",
        detail_url=item.get("detail_url") or "",
        website=item.get("website"),
        sector=item.get("sector"),
        description=item.get("description"),
        linkedin_url=item.get("linkedin_url"),
        photo_url=item.get("photo_url"),
        founders=tuple(_to_founder(f) for f in item.get("founders") or ()),
    )


def _to_founder(item: dict) -> Founder:
    return Founder(name=item.get("name") or "", role=item.get("role"))
