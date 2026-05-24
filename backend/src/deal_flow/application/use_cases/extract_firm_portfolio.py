from dataclasses import dataclass
from urllib.parse import urljoin

from deal_flow.application.ports.services.web_extractor import WebExtractor
from deal_flow.domain.entities.founder import Founder
from deal_flow.domain.entities.portfolio_company import PortfolioCompany


@dataclass(frozen=True)
class ExtractFirmPortfolioInput:
    portfolio_url: str
    limit: int = 10


class ExtractFirmPortfolio:
    """Scrape the portfolio listing, batch-scrape each detail page, merge."""

    def __init__(self, extractor: WebExtractor) -> None:
        self._extractor = extractor

    def execute(self, input: ExtractFirmPortfolioInput) -> list[PortfolioCompany]:
        listings = self._extractor.scrape_portfolio_listing(input.portfolio_url)[: input.limit]

        for item in listings:
            if item.get("detail_url"):
                item["detail_url"] = urljoin(input.portfolio_url, item["detail_url"])

        detail_urls = [item["detail_url"] for item in listings if item.get("detail_url")]
        details_by_url: dict[str, dict] = {}
        if detail_urls:
            payloads = self._extractor.scrape_portfolio_details(detail_urls)
            details_by_url = dict(zip(detail_urls, payloads, strict=False))

        return [
            _to_company(item, details_by_url.get(item.get("detail_url") or ""))
            for item in listings
        ]


def _to_company(listing: dict, detail: dict | None) -> PortfolioCompany:
    detail = detail or {}
    founders = tuple(
        Founder(name=f.get("name") or "", role=f.get("role"))
        for f in (detail.get("founders") or [])
        if f and f.get("name")
    )
    return PortfolioCompany(
        name=listing.get("name") or "",
        detail_url=listing.get("detail_url") or "",
        website=detail.get("website") or listing.get("website"),
        sector=detail.get("sector") or listing.get("sector"),
        description=detail.get("description"),
        linkedin_url=detail.get("linkedin_url"),
        founders=founders,
    )
