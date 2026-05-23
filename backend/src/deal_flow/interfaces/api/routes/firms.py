from fastapi import APIRouter, Depends

from deal_flow.application.ports.services.web_extractor import WebExtractor
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
from deal_flow.interfaces.api.dependencies import (
    get_extract_firm_blog_posts,
    get_extract_firm_partners,
    get_extract_firm_portfolio,
    get_web_extractor,
)

router = APIRouter(prefix="/api/firms", tags=["firms"])


@router.get("/{firm_domain}/sections")
def get_firm_sections(
    firm_domain: str,
    extractor: WebExtractor = Depends(get_web_extractor),
) -> dict[str, str | None]:
    return extractor.discover_firm_sections(firm_domain)


@router.get("/{firm_domain}/partners")
def list_partners(
    firm_domain: str,
    limit: int = 10,
    use_case: ExtractFirmPartners = Depends(get_extract_firm_partners),
) -> list[Partner]:
    return use_case.execute(ExtractFirmPartnersInput(firm_domain=firm_domain, limit=limit))


@router.get("/{firm_domain}/portfolio")
def list_portfolio(
    firm_domain: str,
    limit: int = 10,
    use_case: ExtractFirmPortfolio = Depends(get_extract_firm_portfolio),
) -> list[PortfolioCompany]:
    return use_case.execute(ExtractFirmPortfolioInput(firm_domain=firm_domain, limit=limit))


@router.get("/{firm_domain}/blog-posts")
def list_blog_posts(
    firm_domain: str,
    limit: int = 10,
    use_case: ExtractFirmBlogPosts = Depends(get_extract_firm_blog_posts),
) -> list[BlogPost]:
    return use_case.execute(ExtractFirmBlogPostsInput(firm_domain=firm_domain, limit=limit))
