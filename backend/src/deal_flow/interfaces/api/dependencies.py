"""Composition root — the only module in `interfaces/` that imports
`infrastructure`. Wires the WebExtractor port to its Firecrawl adapter and
hands the use cases to FastAPI via Depends.
"""

from functools import lru_cache

from fastapi import Depends

from deal_flow.application.ports.services.web_extractor import WebExtractor
from deal_flow.application.use_cases.extract_firm_blog_posts import ExtractFirmBlogPosts
from deal_flow.application.use_cases.extract_firm_partners import ExtractFirmPartners
from deal_flow.application.use_cases.extract_firm_portfolio import ExtractFirmPortfolio
from deal_flow.infrastructure.config.settings import Settings, get_settings
from deal_flow.infrastructure.external.firecrawl.extractor import FirecrawlExtractor


@lru_cache
def get_web_extractor(settings: Settings = Depends(get_settings)) -> WebExtractor:
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
