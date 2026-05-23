from dataclasses import dataclass
from urllib.parse import urljoin

from deal_flow.application.ports.services.web_extractor import WebExtractor
from deal_flow.domain.entities.partner import Partner


@dataclass(frozen=True)
class ExtractFirmPartnersInput:
    firm_domain: str
    limit: int = 10


class ExtractFirmPartners:
    """Discover the firm's team page, scrape the partner listing, then
    batch-scrape each profile and merge the results into Partner entities."""

    def __init__(self, extractor: WebExtractor) -> None:
        self._extractor = extractor

    def execute(self, input: ExtractFirmPartnersInput) -> list[Partner]:
        sections = self._extractor.discover_firm_sections(input.firm_domain)
        team_url = sections.get("team")
        if not team_url:
            return []

        listings = self._extractor.scrape_partner_listing(team_url)[: input.limit]

        for item in listings:
            if item.get("profile_url"):
                item["profile_url"] = urljoin(team_url, item["profile_url"])

        detail_urls = [item["profile_url"] for item in listings if item.get("profile_url")]
        details_by_url: dict[str, dict] = {}
        if detail_urls:
            payloads = self._extractor.scrape_partner_details(detail_urls)
            details_by_url = dict(zip(detail_urls, payloads, strict=False))

        return [
            _to_partner(item, details_by_url.get(item.get("profile_url") or ""))
            for item in listings
        ]


def _to_partner(listing: dict, detail: dict | None) -> Partner:
    detail = detail or {}
    return Partner(
        name=listing.get("name") or "",
        profile_url=listing.get("profile_url") or "",
        role=detail.get("role") or listing.get("role"),
        bio=detail.get("bio"),
        linkedin_url=detail.get("linkedin_url") or listing.get("linkedin_url"),
        x_url=detail.get("x_url") or listing.get("x_url"),
        education=tuple(detail.get("education") or ()),
        prior_experience=tuple(detail.get("prior_experience") or ()),
    )
