"""Crawl a firm's public site and emit a firm subgraph."""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.application.ports.web import WebFetcher
from pipeline.application.use_cases.firm_extractors import EXTRACTORS, FirmSubgraph
from pipeline.entities.errors import DomainError
from pipeline.entities.models import BlogPost, Firm
from pipeline.entities.value_objects import Url


@dataclass(frozen=True, slots=True)
class CrawlFirmSite:
    """Discover all partners, companies, and recent essays for a single firm.

    The crawl is intentionally read-only: nothing here writes to storage.
    The composition root is responsible for persisting the returned subgraph.
    """

    web: WebFetcher

    def execute(self, firm: Firm) -> FirmSubgraph:
        extractor = EXTRACTORS[firm.name]

        people_md = _fetch_or_empty(self.web, firm.people_page_url)
        partners = extractor.extract_partners(people_md, firm.people_page_url)

        portfolio_md = _fetch_or_empty(self.web, firm.portfolio_page_url)
        companies = extractor.extract_companies(portfolio_md, firm.portfolio_page_url)

        blog_posts: tuple[BlogPost, ...] = ()
        if firm.blog_url is not None:
            blog_md = _fetch_or_empty(self.web, firm.blog_url)
            blog_posts = tuple(extractor.extract_blog_posts(blog_md, firm.blog_url, partners))

        return FirmSubgraph(
            firm=firm.name,
            partners=tuple(partners),
            companies=tuple(companies),
            founders=(),  # founders are populated by DiscoverHandles + downstream
            blog_posts=blog_posts,
        )


def _fetch_or_empty(web: WebFetcher, url: Url) -> str:
    """Treat per-page fetch failures as recoverable: a missing blog is not fatal."""
    try:
        return web.fetch_markdown(url)
    except DomainError:
        return ""
