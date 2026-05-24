from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException

from deal_flow.application.use_cases.enrich_partner_with_twitter import (
    EnrichPartnerWithTwitter,
    EnrichPartnerWithTwitterInput,
    handle_from_x_url,
)
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
from deal_flow.application.use_cases.search_partner_form_d_filings import (
    SearchPartnerFormDFilings,
    SearchPartnerFormDFilingsInput,
)
from deal_flow.domain.entities.blog_post import BlogPost
from deal_flow.domain.entities.partner import Partner
from deal_flow.domain.entities.partner_form_d_signal import PartnerFormDSignal
from deal_flow.domain.entities.portfolio_company import PortfolioCompany
from deal_flow.domain.value_objects.date_range import DateRange
from deal_flow.infrastructure.external.firms_registry import FirmSources
from deal_flow.interfaces.api.dependencies import (
    get_enrich_partner_with_twitter,
    get_extract_firm_blog_posts,
    get_extract_firm_partners,
    get_extract_firm_portfolio,
    get_firms_registry,
    get_search_partner_form_d_filings,
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


@router.get("/{firm_domain}/partners/{handle}/twitter")
def get_partner_with_twitter(
    firm_domain: str,
    handle: str,
    max_tweets: int = 100,
    max_followings: int = 200,
    max_mentions: int = 40,
    registry: dict[str, FirmSources] = Depends(get_firms_registry),
    extract: ExtractFirmPartners = Depends(get_extract_firm_partners),
    enrich: EnrichPartnerWithTwitter = Depends(get_enrich_partner_with_twitter),
) -> Partner:
    """Enrich one named partner with their raw Twitter signals.

    The handle is matched against the partner's Firecrawl-extracted ``x_url``;
    if no partner on the firm's team page has that handle, we 404 *before*
    spending any twitterapi.io credits.
    """
    sources = _resolve(firm_domain, registry)
    if not sources.team_url:
        raise HTTPException(
            status_code=404,
            detail=f"firm '{firm_domain}' has no team_url in firms.yaml",
        )
    needle = handle.lower().lstrip("@")
    partners = extract.execute(
        ExtractFirmPartnersInput(team_url=sources.team_url, limit=50)
    )
    target = next(
        (p for p in partners if handle_from_x_url(p.x_url) == needle),
        None,
    )
    if target is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"no partner with twitter handle '{handle}' found on "
                f"{firm_domain}'s team page"
            ),
        )
    return enrich.execute(
        EnrichPartnerWithTwitterInput(
            partner=target,
            max_tweets=max_tweets,
            max_followings=max_followings,
            max_mentions=max_mentions,
        )
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


@router.get("/{firm_domain}/edgar-signals")
def list_edgar_signals(
    firm_domain: str,
    days: int = 90,
    limit: int = 10,
    registry: dict[str, FirmSources] = Depends(get_firms_registry),
    extract_partners: ExtractFirmPartners = Depends(get_extract_firm_partners),
    search_filings: SearchPartnerFormDFilings = Depends(
        get_search_partner_form_d_filings
    ),
) -> list[PartnerFormDSignal]:
    sources = _resolve(firm_domain, registry)
    if not sources.team_url:
        return []
    partners = extract_partners.execute(
        ExtractFirmPartnersInput(team_url=sources.team_url, limit=limit)
    )
    today = date.today()
    window = DateRange(start=today - timedelta(days=days), end=today)
    return [
        search_filings.execute(
            SearchPartnerFormDFilingsInput(partner_name=p.name, date_range=window)
        )
        for p in partners
        if p.name
    ]
