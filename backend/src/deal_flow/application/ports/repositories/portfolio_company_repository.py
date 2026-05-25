from abc import ABC, abstractmethod

from deal_flow.domain.entities.portfolio_company import PortfolioCompany


class PortfolioCompanyRepository(ABC):
    """Read access to persisted portfolio company data (the scraped JSON sitting
    in ``backend/data/``). Distinct from the live-scrape path used by
    ``ExtractFirmPortfolio`` — this repo serves the snapshot, fast and offline.
    """

    @abstractmethod
    def list_by_firm(self, firm_domain: str) -> list[PortfolioCompany]:
        """Return all known portfolio companies for ``firm_domain`` (e.g.
        ``"a16z.com"``). Empty list if the firm has no persisted data."""
