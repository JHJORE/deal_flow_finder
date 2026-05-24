from fastapi import APIRouter, Depends, HTTPException

from deal_flow.application.use_cases.extract_firm_blog_posts import (
    ExtractFirmBlogPosts,
    ExtractFirmBlogPostsInput,
)
from deal_flow.application.use_cases.extract_firm_partners import (
    ExtractFirmPartners,
    ExtractFirmPartnersInput,
)
from deal_flow.application.use_cases.extract_firm_portfolio import (
    ExtractFirmPortfolio,
    ExtractFirmPortfolioInput,
)
from deal_flow.domain.entities.blog_post import BlogPost
from deal_flow.domain.entities.partner import Partner
from deal_flow.domain.entities.portfolio_company import PortfolioCompany
from deal_flow.infrastructure.external.firms_registry import FirmSources
from deal_flow.interfaces.api.dependencies import (
    get_extract_firm_blog_posts,
    get_extract_firm_partners,
    get_extract_firm_portfolio,
    get_firms_registry,
)

router = APIRouter(prefix="/api/firms", tags=["firms"])


def _resolve(firm_domain: str, registry: dict[str, FirmSources]) -> FirmSources:
    sources = registry.get(firm_domain)
    if sources is None:
        raise HTTPException(
            status_code=404,
            detail=f"firm '{firm_domain}' not in backend/firms.yaml",
        )
    return sources


@router.get("/{firm_domain}/partners")
def list_partners(
    firm_domain: str,
    limit: int = 10,
    registry: dict[str, FirmSources] = Depends(get_firms_registry),
    use_case: ExtractFirmPartners = Depends(get_extract_firm_partners),
) -> list[Partner]:
    sources = _resolve(firm_domain, registry)
    if not sources.team_url:
        return []
    return use_case.execute(
        ExtractFirmPartnersInput(team_url=sources.team_url, limit=limit)
    )


@router.get("/{firm_domain}/portfolio")
def list_portfolio(
    firm_domain: str,
    limit: int = 10,
    registry: dict[str, FirmSources] = Depends(get_firms_registry),
    use_case: ExtractFirmPortfolio = Depends(get_extract_firm_portfolio),
) -> list[PortfolioCompany]:
    sources = _resolve(firm_domain, registry)
    if not sources.portfolio_url:
        return []
    return use_case.execute(
        ExtractFirmPortfolioInput(portfolio_url=sources.portfolio_url, limit=limit)
    )


@router.get("/{firm_domain}/blog-posts")
def list_blog_posts(
    firm_domain: str,
    limit: int = 10,
    registry: dict[str, FirmSources] = Depends(get_firms_registry),
    use_case: ExtractFirmBlogPosts = Depends(get_extract_firm_blog_posts),
) -> list[BlogPost]:
    sources = _resolve(firm_domain, registry)
    if not sources.blog_url:
        return []
    return use_case.execute(
        ExtractFirmBlogPostsInput(blog_url=sources.blog_url, limit=limit)
    )
