from abc import ABC, abstractmethod


class WebExtractor(ABC):
    """The one port use cases use to read public web pages.

    Methods are purpose-shaped (not generic primitives). Each returns plain
    Python dicts — schemas/prompts live in the infrastructure adapter so the
    application layer needn't know what shape they take. Application code
    handles the orchestration (URL resolution, merging, capping).
    """

    @abstractmethod
    def discover_firm_sections(self, firm_domain: str) -> dict[str, str | None]:
        """Return ``{"team": url|None, "portfolio": url|None, "blog": url|None}``."""

    @abstractmethod
    def scrape_partner_listing(self, team_url: str) -> list[dict]:
        ...

    @abstractmethod
    def scrape_partner_details(self, profile_urls: list[str]) -> list[dict]:
        """Same order as ``profile_urls``; ``{}`` for any URL we couldn't enrich."""

    @abstractmethod
    def scrape_portfolio_listing(self, portfolio_url: str) -> list[dict]:
        ...

    @abstractmethod
    def scrape_portfolio_details(self, detail_urls: list[str]) -> list[dict]:
        ...

    @abstractmethod
    def scrape_blog_posts(self, blog_url: str) -> list[dict]:
        ...
