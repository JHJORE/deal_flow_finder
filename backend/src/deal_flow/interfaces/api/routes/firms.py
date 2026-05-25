from dataclasses import asdict, replace
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException

from deal_flow.application.use_cases.analyze_partner_linkedin_signals import (
    AnalyzePartnerLinkedInSignals,
)
from deal_flow.application.use_cases.analyze_partner_twitter_signals import (
    AnalyzePartnerTwitterSignals,
    AnalyzePartnerTwitterSignalsInput,
    PreviousFollowings,
)
from deal_flow.application.use_cases.enrich_firm_partners_with_linkedin import (
    EnrichFirmPartnersWithLinkedIn,
    EnrichFirmPartnersWithLinkedInInput,
)
from deal_flow.application.use_cases.enrich_firm_portfolio_with_linkedin import (
    EnrichPortfolioCompaniesWithLinkedIn,
    EnrichPortfolioCompaniesWithLinkedInInput,
)
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
from deal_flow.infrastructure.persistence.output_store import OutputStore, slugify
from deal_flow.interfaces.api.dependencies import (
    get_analyze_partner_linkedin_signals,
    get_analyze_partner_twitter_signals,
    get_enrich_firm_partners_with_linkedin,
    get_enrich_partner_with_twitter,
    get_enrich_portfolio_companies_with_linkedin,
    get_extract_firm_blog_posts,
    get_extract_firm_partners,
    get_extract_firm_portfolio,
    get_firms_registry,
    get_output_store,
    get_search_partner_form_d_filings,
)

router = APIRouter(prefix="/firms", tags=["firms"])


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
    outputs: OutputStore = Depends(get_output_store),
) -> list[Partner]:
    sources = _resolve(firm_domain, registry)
    if not sources.team_urls and not sources.team_payload_url:
        return []
    partners = use_case.execute(
        ExtractFirmPartnersInput(
            team_urls=sources.team_urls,
            payload_url=sources.team_payload_url,
            payload_attribute=sources.team_payload_attribute,
            payload_role_filter=sources.team_payload_role_filter,
            limit=limit,
            firm_name=firm_domain.split(".")[0],
        )
    )
    outputs.write([asdict(p) for p in partners], "firms", firm_domain, "partners.json")
    return partners


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


@router.get("/{firm_domain}/partners/linkedin")
def list_partners_with_linkedin(
    firm_domain: str,
    max_posts: int = 20,
    include_reactions: bool = False,
    include_comments: bool = False,
    max_reactions: int = 5,
    max_comments: int = 5,
    posted_limit: str | None = None,
    use_case: EnrichFirmPartnersWithLinkedIn = Depends(
        get_enrich_firm_partners_with_linkedin
    ),
    outputs: OutputStore = Depends(get_output_store),
) -> list[Partner]:
    """Batch-enrich every partner in the firm's directory with LinkedIn
    activity. One Apify run per call (the adapter caches per-URL so repeat
    calls don't re-spend credits).
    """
    try:
        enriched = use_case.execute(
            EnrichFirmPartnersWithLinkedInInput(
                firm_domain=firm_domain,
                max_posts=max_posts,
                include_reactions=include_reactions,
                include_comments=include_comments,
                max_reactions=max_reactions,
                max_comments=max_comments,
                posted_limit=posted_limit,
            )
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    outputs.write(
        [asdict(p) for p in enriched],
        "firms", firm_domain, "partners-linkedin.json",
    )
    for p in enriched:
        if p.linkedin is not None:
            outputs.write(
                asdict(p),
                "firms", firm_domain, "partners", slugify(p.name), "linkedin.json",
            )
    return enriched


@router.get("/{firm_domain}/portfolio/linkedin")
def list_portfolio_with_linkedin(
    firm_domain: str,
    limit: int = 50,
    max_posts: int = 20,
    include_reactions: bool = False,
    include_comments: bool = False,
    max_reactions: int = 5,
    max_comments: int = 5,
    posted_limit: str | None = None,
    registry: dict[str, FirmSources] = Depends(get_firms_registry),
    extract: ExtractFirmPortfolio = Depends(get_extract_firm_portfolio),
    enrich: EnrichPortfolioCompaniesWithLinkedIn = Depends(
        get_enrich_portfolio_companies_with_linkedin
    ),
    outputs: OutputStore = Depends(get_output_store),
) -> list[PortfolioCompany]:
    """Discover the firm's portfolio (live Firecrawl) and batch-enrich
    companies that already carry a ``linkedin_url`` with their LinkedIn
    activity. Companies without a LinkedIn URL pass through unchanged.
    """
    sources = _resolve(firm_domain, registry)
    if not sources.portfolio_url:
        return []
    companies = extract.execute(
        ExtractFirmPortfolioInput(
            portfolio_url=sources.portfolio_url,
            limit=limit,
            sitemap_url=sources.portfolio_sitemap_url,
            html_json_url=sources.portfolio_html_json_url,
            html_json_attribute=sources.portfolio_html_json_attribute,
        )
    )
    enriched = enrich.execute(
        EnrichPortfolioCompaniesWithLinkedInInput(
            companies=companies,
            max_posts=max_posts,
            include_reactions=include_reactions,
            include_comments=include_comments,
            max_reactions=max_reactions,
            max_comments=max_comments,
            posted_limit=posted_limit,
        )
    )
    outputs.write(
        [asdict(c) for c in enriched],
        "firms", firm_domain, "portfolio-linkedin.json",
    )
    for c in enriched:
        if c.linkedin is not None:
            outputs.write(
                asdict(c),
                "firms", firm_domain, "portfolio", slugify(c.name), "linkedin.json",
            )
    return enriched


@router.get("/{firm_domain}/partners/{handle}/linkedin")
def get_partner_with_linkedin(
    firm_domain: str,
    handle: str,
    max_posts: int = 20,
    include_reactions: bool = False,
    include_comments: bool = False,
    max_reactions: int = 5,
    max_comments: int = 5,
    posted_limit: str | None = None,
    analyze: bool = True,
    use_case: EnrichFirmPartnersWithLinkedIn = Depends(
        get_enrich_firm_partners_with_linkedin
    ),
    analyzer: AnalyzePartnerLinkedInSignals = Depends(
        get_analyze_partner_linkedin_signals
    ),
    outputs: OutputStore = Depends(get_output_store),
) -> Partner:
    """Enrich one partner with LinkedIn posts and (by default) run the
    two-stage Gemini analysis to extract per-post themes and a
    partner-level theme summary. Pass ``?analyze=false`` to skip the LLM
    step (raw posts only)."""
    try:
        enriched = use_case.execute(
            EnrichFirmPartnersWithLinkedInInput(
                firm_domain=firm_domain,
                max_posts=max_posts,
                include_reactions=include_reactions,
                include_comments=include_comments,
                max_reactions=max_reactions,
                max_comments=max_comments,
                posted_limit=posted_limit,
                target_handle=handle,
            )
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not enriched:
        raise HTTPException(
            status_code=404,
            detail=f"no partner with linkedin handle '{handle}' in {firm_domain}",
        )
    target = enriched[0]
    if analyze and target.linkedin is not None:
        analysis = analyzer.execute(target.linkedin)
        target = replace(
            target, linkedin=replace(target.linkedin, analysis=analysis)
        )
    outputs.write(
        asdict(target),
        "firms", firm_domain, "partners", slugify(target.name or handle), "linkedin.json",
    )
    return target


@router.get("/{firm_domain}/partners/{handle}/twitter")
def get_partner_with_twitter(
    firm_domain: str,
    handle: str,
    max_tweets: int = 100,
    max_followings: int = 200,
    max_mentions: int = 40,
    analyze: bool = True,
    registry: dict[str, FirmSources] = Depends(get_firms_registry),
    extract: ExtractFirmPartners = Depends(get_extract_firm_partners),
    enrich: EnrichPartnerWithTwitter = Depends(get_enrich_partner_with_twitter),
    analyzer: AnalyzePartnerTwitterSignals = Depends(
        get_analyze_partner_twitter_signals
    ),
    outputs: OutputStore = Depends(get_output_store),
) -> Partner:
    """Enrich one named partner with their raw Twitter signals, then run the
    LLM thematisation + newly-following diff against the previously persisted
    snapshot.

    The handle is matched against the partner's Firecrawl-extracted ``x_url``;
    if no partner on the firm's team page has that handle, we 404 *before*
    spending any twitterapi.io credits.

    Pass ``?analyze=false`` to skip the LLM step (raw signals only).
    """
    sources = _resolve(firm_domain, registry)
    if not sources.team_urls and not sources.team_payload_url:
        raise HTTPException(
            status_code=404,
            detail=f"firm '{firm_domain}' has no team listing in firms.yaml",
        )
    needle = handle.lower().lstrip("@")
    partners = extract.execute(
        ExtractFirmPartnersInput(
            team_urls=sources.team_urls,
            payload_url=sources.team_payload_url,
            payload_attribute=sources.team_payload_attribute,
            payload_role_filter=sources.team_payload_role_filter,
            limit=50,
            firm_name=firm_domain.split(".")[0],
        )
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
    target_slug = slugify(target.name or handle)
    previous = _load_previous_followings(
        outputs, firm_domain, target_slug,
    )
    enriched = enrich.execute(
        EnrichPartnerWithTwitterInput(
            partner=target,
            max_tweets=max_tweets,
            max_followings=max_followings,
            max_mentions=max_mentions,
        )
    )
    if analyze and enriched.twitter is not None:
        analysis = analyzer.execute(
            AnalyzePartnerTwitterSignalsInput(
                snapshot=enriched.twitter,
                previous=previous,
            )
        )
        enriched = replace(
            enriched, twitter=replace(enriched.twitter, analysis=analysis)
        )
    outputs.write(
        asdict(enriched),
        "firms", firm_domain, "partners", target_slug, "twitter.json",
    )
    return enriched


def _load_previous_followings(
    outputs: OutputStore, firm_domain: str, partner_slug: str
) -> PreviousFollowings:
    """Read the previously persisted ``twitter.json`` for this partner and
    pull just the followings list. Returns an empty baseline on first run."""
    raw = outputs.read(
        "firms", firm_domain, "partners", partner_slug, "twitter.json"
    )
    if not isinstance(raw, dict):
        return PreviousFollowings.empty()
    twitter = raw.get("twitter") or {}
    followings = twitter.get("followings") or []
    user_ids: set[str] = set()
    handles: set[str] = set()
    for entry in followings:
        if not isinstance(entry, dict):
            continue
        uid = entry.get("user_id")
        if isinstance(uid, str) and uid:
            user_ids.add(uid)
        h = entry.get("handle")
        if isinstance(h, str) and h:
            handles.add(h)
    return PreviousFollowings(
        user_ids=frozenset(user_ids), handles=frozenset(handles)
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
    outputs: OutputStore = Depends(get_output_store),
) -> list[PartnerFormDSignal]:
    sources = _resolve(firm_domain, registry)
    if not sources.team_urls and not sources.team_payload_url:
        return []
    partners = extract_partners.execute(
        ExtractFirmPartnersInput(
            team_urls=sources.team_urls,
            payload_url=sources.team_payload_url,
            payload_attribute=sources.team_payload_attribute,
            payload_role_filter=sources.team_payload_role_filter,
            limit=limit,
            firm_name=firm_domain.split(".")[0],
        )
    )
    today = date.today()
    window = DateRange(start=today - timedelta(days=days), end=today)
    signals: list[PartnerFormDSignal] = []
    for p in partners:
        if not p.name:
            continue
        sig = search_filings.execute(
            SearchPartnerFormDFilingsInput(partner_name=p.name, date_range=window)
        )
        outputs.write(
            asdict(sig),
            "firms", firm_domain, "partners", slugify(p.name), "edgar.json",
        )
        signals.append(sig)
    return signals
