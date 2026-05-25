from dataclasses import dataclass

from deal_flow.application.ports.repositories.portfolio_company_repository import (
    PortfolioCompanyRepository,
)
from deal_flow.domain.entities.portfolio_company import PortfolioCompany


@dataclass(frozen=True)
class LoadFirmPortfolioCompaniesInput:
    firm_domain: str


class LoadFirmPortfolioCompanies:
    """Read persisted portfolio companies for a firm.

    Companion to ``LoadFirmPartnerProfiles``. The request path stays cheap —
    JSON snapshot only, no live scraping.
    """

    def __init__(self, repo: PortfolioCompanyRepository) -> None:
        self._repo = repo

    def execute(self, input: LoadFirmPortfolioCompaniesInput) -> list[PortfolioCompany]:
        return self._repo.list_by_firm(input.firm_domain)
