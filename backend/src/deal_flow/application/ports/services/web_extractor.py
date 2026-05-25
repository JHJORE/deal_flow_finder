from abc import ABC, abstractmethod


class WebExtractor(ABC):
    """The one port use cases use to read public web pages.

    Methods are purpose-shaped (not generic primitives). Each returns plain
    Python dicts — schemas/prompts live in the infrastructure adapter so the
    application layer needn't know what shape they take. Application code
    handles the orchestration (URL resolution, merging, capping).
    """

    @abstractmethod
    def scrape_partner_listing(self, team_url: str) -> list[dict]:
        ...

    @abstractmethod
    def scrape_partner_details(self, profile_urls: list[str]) -> dict[str, dict]:
        """Keyed by the URL actually scraped. A URL may be absent if the
        backing scraper couldn't enrich it."""

    @abstractmethod
    def scrape_portfolio_listing(self, portfolio_url: str) -> list[dict]:
        ...

    @abstractmethod
    def discover_portfolio_from_html_json(
        self, listing_url: str, attribute_name: str, limit: int
    ) -> list[dict]:
        """Some firms (e.g. a16z) embed their entire portfolio as a JSON blob
        in a ``data-*`` attribute on the listing page. Returns up to ``limit``
        full PortfolioCompany-shaped dicts directly — no detail scrape needed,
        no LLM, no Firecrawl. Bypasses all the JS-rendering / hallucination
        risk of an LLM-driven listing scrape."""

    @abstractmethod
    def discover_portfolio_urls_from_sitemap(
        self, sitemap_url: str, limit: int
    ) -> list[dict]:
        """Read a sitemap XML and return up to ``limit`` listing-shaped dicts
        (``name``, ``detail_url``). Names are derived from the URL slug, since
        sitemaps don't carry display names. Bypasses JS rendering entirely —
        useful when a firm's portfolio listing page is JS-heavy or behind a
        bot wall."""

    @abstractmethod
    def scrape_portfolio_details(self, detail_urls: list[str]) -> dict[str, dict]:
        """Keyed by the URL actually scraped. A URL may be absent if the
        backing scraper couldn't enrich it."""

    @abstractmethod
    def scrape_blog_posts(self, blog_url: str) -> list[dict]:
        ...

    @abstractmethod
    def search_x_profile(self, firm_name: str, partner_name: str) -> str | None:
        """Find the partner's X/Twitter profile URL via web search.

        Returns the full ``https://x.com/<handle>`` URL on success, ``None`` if
        no plausible match. Used as a fallback when the team-page scrape didn't
        pick up an X link for the partner."""
