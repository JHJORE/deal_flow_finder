"""Composition root — the only module in `interfaces/` that imports
`infrastructure`. Wires ports to concrete adapters and hands use cases to
FastAPI via Depends.
"""

from functools import lru_cache

from fastapi import Depends

from deal_flow.application.ports.repositories.board_seat_log import BoardSeatLog
from deal_flow.application.ports.repositories.partner_directory import (
    PartnerDirectory,
)
from deal_flow.application.ports.repositories.partner_profile_repository import (
    PartnerProfileRepository,
)
from deal_flow.application.ports.repositories.portfolio_company_repository import (
    PortfolioCompanyRepository,
)
from deal_flow.application.ports.services.linkedin_collector import LinkedInCollector
from deal_flow.application.ports.services.llm_structured_output import (
    LlmStructuredOutput,
)
from deal_flow.application.ports.services.sec_filing_searcher import (
    SecFilingSearcher,
)
from deal_flow.application.ports.services.twitter_collector import TwitterCollector
from deal_flow.application.ports.services.web_extractor import WebExtractor
from deal_flow.application.use_cases.aggregate_item_themes import (
    AggregateItemThemes,
)
from deal_flow.application.use_cases.analyze_partner_linkedin_signals import (
    AnalyzePartnerLinkedInSignals,
)
from deal_flow.application.use_cases.analyze_partner_twitter_signals import (
    AnalyzePartnerTwitterSignals,
)
from deal_flow.application.use_cases.enrich_firm_partners_with_linkedin import (
    EnrichFirmPartnersWithLinkedIn,
)
from deal_flow.application.use_cases.enrich_firm_portfolio_with_linkedin import (
    EnrichPortfolioCompaniesWithLinkedIn,
)
from deal_flow.application.use_cases.enrich_partner_with_twitter import (
    EnrichPartnerWithTwitter,
)
from deal_flow.application.use_cases.extract_firm_blog_posts import ExtractFirmBlogPosts
from deal_flow.application.use_cases.extract_firm_partners import ExtractFirmPartners
from deal_flow.application.use_cases.extract_firm_portfolio import ExtractFirmPortfolio
from deal_flow.application.use_cases.load_firm_partner_profiles import (
    LoadFirmPartnerProfiles,
)
from deal_flow.application.use_cases.load_firm_portfolio_companies import (
    LoadFirmPortfolioCompanies,
)
from deal_flow.application.use_cases.search_partner_form_d_filings import (
    SearchPartnerFormDFilings,
)
from deal_flow.application.use_cases.summarize_partner_bio import SummarizePartnerBio
from deal_flow.application.use_cases.thematize_items import ThematizeItems
import psycopg

from deal_flow.infrastructure.config.settings import get_settings
from deal_flow.infrastructure.db.connection import get_connection
from deal_flow.infrastructure.external.apify.linkedin_posts_collector import (
    HarvestApiLinkedInCollector,
)
from deal_flow.infrastructure.external.edgar.searcher import EdgarFullTextSearcher
from deal_flow.infrastructure.external.firecrawl.extractor import FirecrawlExtractor
from deal_flow.infrastructure.external.firms_registry import FirmSources, load_registry
from deal_flow.infrastructure.external.gemini.client import GeminiStructuredOutput
from deal_flow.infrastructure.external.twitterapi.collector import TwitterApiCollector
from deal_flow.infrastructure.persistence.file_board_seat_log import FileBoardSeatLog
from deal_flow.infrastructure.persistence.file_partner_directory import (
    FilePartnerDirectory,
)
from deal_flow.infrastructure.persistence.output_store import OutputStore
from deal_flow.infrastructure.persistence.postgres_partner_profile_repository import (
    PostgresPartnerProfileRepository,
)
from deal_flow.infrastructure.persistence.postgres_portfolio_company_repository import (
    PostgresPortfolioCompanyRepository,
)


@lru_cache
def get_firms_registry() -> dict[str, FirmSources]:
    return load_registry()


@lru_cache
def get_output_store() -> OutputStore:
    return OutputStore(get_settings().output_dir)


@lru_cache
def get_web_extractor() -> WebExtractor:
    settings = get_settings()
    return FirecrawlExtractor(
        api_key=settings.firecrawl_api_key,
        cache_dir=settings.firecrawl_cache_dir,
        refresh=settings.firecrawl_cache_refresh,
    )


def get_extract_firm_partners(
    extractor: WebExtractor = Depends(get_web_extractor),
) -> ExtractFirmPartners:
    return ExtractFirmPartners(extractor=extractor)


def get_extract_firm_portfolio(
    extractor: WebExtractor = Depends(get_web_extractor),
) -> ExtractFirmPortfolio:
    return ExtractFirmPortfolio(extractor=extractor)


def get_extract_firm_blog_posts(
    extractor: WebExtractor = Depends(get_web_extractor),
) -> ExtractFirmBlogPosts:
    return ExtractFirmBlogPosts(extractor=extractor)


@lru_cache
def get_sec_filing_searcher() -> SecFilingSearcher:
    settings = get_settings()
    return EdgarFullTextSearcher(
        user_agent=settings.sec_user_agent,
        cache_dir=settings.sec_cache_dir / ".cache",
        refresh=settings.sec_cache_refresh,
    )


def get_board_seat_log(firm_domain: str) -> BoardSeatLog:
    """Per-firm log so each firm gets its own curated output file at
    ``.outputs/firms/{firm_domain}/board_seats.json``. ``firm_domain`` is
    pulled from the route's path params by FastAPI.
    """
    settings = get_settings()
    return FileBoardSeatLog(
        path=settings.output_dir / "firms" / firm_domain / "board_seats.json",
    )


def get_search_partner_form_d_filings(
    searcher: SecFilingSearcher = Depends(get_sec_filing_searcher),
    log: BoardSeatLog = Depends(get_board_seat_log),
) -> SearchPartnerFormDFilings:
    return SearchPartnerFormDFilings(searcher=searcher, log=log)


@lru_cache
def get_twitter_collector() -> TwitterCollector:
    settings = get_settings()
    return TwitterApiCollector(
        api_key=settings.twitterapi_io_key,
        cache_dir=settings.twitterapi_cache_dir,
        refresh=settings.twitterapi_cache_refresh,
    )


def get_enrich_partner_with_twitter(
    collector: TwitterCollector = Depends(get_twitter_collector),
) -> EnrichPartnerWithTwitter:
    return EnrichPartnerWithTwitter(collector=collector)


@lru_cache
def get_linkedin_collector() -> LinkedInCollector:
    settings = get_settings()
    return HarvestApiLinkedInCollector(
        api_token=settings.apify_api_token,
        actor_id=settings.apify_linkedin_actor_id,
        cache_dir=settings.apify_cache_dir,
        refresh=settings.apify_cache_refresh,
    )


@lru_cache
def get_partner_directory() -> PartnerDirectory:
    return FilePartnerDirectory(data_dir=get_settings().partner_data_dir)


def get_enrich_firm_partners_with_linkedin(
    directory: PartnerDirectory = Depends(get_partner_directory),
    collector: LinkedInCollector = Depends(get_linkedin_collector),
) -> EnrichFirmPartnersWithLinkedIn:
    return EnrichFirmPartnersWithLinkedIn(directory=directory, collector=collector)


def get_enrich_portfolio_companies_with_linkedin(
    collector: LinkedInCollector = Depends(get_linkedin_collector),
) -> EnrichPortfolioCompaniesWithLinkedIn:
    return EnrichPortfolioCompaniesWithLinkedIn(collector=collector)


@lru_cache
def get_llm_structured_output() -> LlmStructuredOutput:
    settings = get_settings()
    return GeminiStructuredOutput(
        api_key=settings.gemini_api_key,
        cache_dir=settings.gemini_cache_dir,
        refresh=settings.gemini_cache_refresh,
    )


def get_partner_profile_repository(
    conn: psycopg.Connection = Depends(get_connection),
) -> PartnerProfileRepository:
    return PostgresPartnerProfileRepository(conn=conn)


def get_summarize_partner_bio(
    llm: LlmStructuredOutput = Depends(get_llm_structured_output),
) -> SummarizePartnerBio:
    return SummarizePartnerBio(llm=llm)


def get_thematize_items(
    llm: LlmStructuredOutput = Depends(get_llm_structured_output),
) -> ThematizeItems:
    return ThematizeItems(llm=llm)


def get_aggregate_item_themes(
    llm: LlmStructuredOutput = Depends(get_llm_structured_output),
) -> AggregateItemThemes:
    return AggregateItemThemes(llm=llm)


def get_analyze_partner_twitter_signals(
    thematize: ThematizeItems = Depends(get_thematize_items),
    aggregate: AggregateItemThemes = Depends(get_aggregate_item_themes),
) -> AnalyzePartnerTwitterSignals:
    return AnalyzePartnerTwitterSignals(thematize=thematize, aggregate=aggregate)


def get_analyze_partner_linkedin_signals(
    thematize: ThematizeItems = Depends(get_thematize_items),
    aggregate: AggregateItemThemes = Depends(get_aggregate_item_themes),
) -> AnalyzePartnerLinkedInSignals:
    return AnalyzePartnerLinkedInSignals(thematize=thematize, aggregate=aggregate)


def get_load_firm_partner_profiles(
    repo: PartnerProfileRepository = Depends(get_partner_profile_repository),
) -> LoadFirmPartnerProfiles:
    return LoadFirmPartnerProfiles(repo=repo)


def get_portfolio_company_repository(
    conn: psycopg.Connection = Depends(get_connection),
) -> PortfolioCompanyRepository:
    return PostgresPortfolioCompanyRepository(conn=conn)


def get_load_firm_portfolio_companies(
    repo: PortfolioCompanyRepository = Depends(get_portfolio_company_repository),
) -> LoadFirmPortfolioCompanies:
    return LoadFirmPortfolioCompanies(repo=repo)
