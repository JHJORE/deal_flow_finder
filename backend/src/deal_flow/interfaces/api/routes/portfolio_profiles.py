from fastapi import APIRouter, Depends

from deal_flow.application.use_cases.load_firm_portfolio_companies import (
    LoadFirmPortfolioCompanies,
    LoadFirmPortfolioCompaniesInput,
)
from deal_flow.domain.entities.portfolio_company import PortfolioCompany
from deal_flow.interfaces.api.dependencies import get_load_firm_portfolio_companies

router = APIRouter(prefix="/api/firms", tags=["portfolio-profiles"])


@router.get("/{firm_domain}/portfolio-profiles")
def list_portfolio_profiles(
    firm_domain: str,
    use_case: LoadFirmPortfolioCompanies = Depends(get_load_firm_portfolio_companies),
) -> list[PortfolioCompany]:
    return use_case.execute(LoadFirmPortfolioCompaniesInput(firm_domain=firm_domain))
