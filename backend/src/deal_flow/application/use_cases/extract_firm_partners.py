from dataclasses import dataclass, replace
from urllib.parse import urljoin

from deal_flow.application.ports.services.web_extractor import WebExtractor
from deal_flow.domain.entities.partner import Partner


@dataclass(frozen=True)
class ExtractFirmPartnersInput:
    team_url: str
    limit: int = 10
    firm_name: str | None = None  # when set, missing x_urls are searched for


class ExtractFirmPartners:
    """Scrape the team listing, batch-scrape each profile, merge into Partners.

    When ``input.firm_name`` is provided, partners whose team-page profile
    didn't surface an X link get one filled in via the extractor's web-search
    fallback. Without ``firm_name`` the fallback is skipped (cheap path).
    """

    def __init__(self, extractor: WebExtractor) -> None:
        self._extractor = extractor

    def execute(self, input: ExtractFirmPartnersInput) -> list[Partner]:
        listings = self._extractor.scrape_partner_listing(input.team_url)[: input.limit]

        for item in listings:
            if item.get("profile_url"):
                item["profile_url"] = urljoin(input.team_url, item["profile_url"])

        detail_urls = [item["profile_url"] for item in listings if item.get("profile_url")]
        details_by_url: dict[str, dict] = (
            self._extractor.scrape_partner_details(detail_urls) if detail_urls else {}
        )

        partners = [
            _to_partner(item, details_by_url.get(item.get("profile_url") or ""))
            for item in listings
        ]
        if input.firm_name:
            partners = [self._fill_x_url(p, input.firm_name) for p in partners]
        return partners

    def _fill_x_url(self, partner: Partner, firm_name: str) -> Partner:
        if partner.x_url or not partner.name:
            return partner
        found = self._extractor.search_x_profile(firm_name, partner.name)
        return replace(partner, x_url=found) if found else partner


def _to_partner(listing: dict, detail: dict | None) -> Partner:
    detail = detail or {}
    return Partner(
        name=listing.get("name") or "",
        profile_url=listing.get("profile_url") or "",
        role=detail.get("role") or listing.get("role"),
        bio=detail.get("bio"),
        linkedin_url=detail.get("linkedin_url") or listing.get("linkedin_url"),
        x_url=detail.get("x_url") or listing.get("x_url"),
        email=detail.get("email"),
        photo_url=detail.get("photo_url"),
        education=tuple(detail.get("education") or ()),
        prior_experience=tuple(detail.get("prior_experience") or ()),
    )
