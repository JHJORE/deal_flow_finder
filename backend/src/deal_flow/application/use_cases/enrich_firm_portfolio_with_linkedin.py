from dataclasses import dataclass, replace
from datetime import UTC, datetime

from deal_flow.application.ports.services.linkedin_collector import LinkedInCollector
from deal_flow.application.use_cases.linkedin_post_mapping import to_snapshot
from deal_flow.domain.entities.portfolio_company import PortfolioCompany


@dataclass(frozen=True)
class EnrichPortfolioCompaniesWithLinkedInInput:
    companies: list[PortfolioCompany]
    max_posts: int = 20
    include_reactions: bool = False
    include_comments: bool = False
    max_reactions: int = 5
    max_comments: int = 5
    posted_limit: str | None = None


class EnrichPortfolioCompaniesWithLinkedIn:
    """Attach LinkedIn activity to each portfolio company that has a
    ``linkedin_url``. Discovery of the companies themselves is left to the
    caller (typically ``ExtractFirmPortfolio``) — this use case is the
    LinkedIn-fanout half only, so it stays composable.
    """

    def __init__(self, collector: LinkedInCollector) -> None:
        self._collector = collector

    def execute(
        self, input: EnrichPortfolioCompaniesWithLinkedInInput
    ) -> list[PortfolioCompany]:
        urls = [c.linkedin_url for c in input.companies if c.linkedin_url]
        if not urls:
            return list(input.companies)

        posts_by_url = self._collector.fetch_posts(
            urls,
            max_posts=input.max_posts,
            include_reactions=input.include_reactions,
            include_comments=input.include_comments,
            max_reactions=input.max_reactions,
            max_comments=input.max_comments,
            posted_limit=input.posted_limit,
        )
        now = datetime.now(UTC)

        enriched: list[PortfolioCompany] = []
        for c in input.companies:
            if not c.linkedin_url or c.linkedin_url not in posts_by_url:
                enriched.append(c)
                continue
            snapshot = to_snapshot(
                c.linkedin_url, posts_by_url[c.linkedin_url], collected_at=now
            )
            enriched.append(replace(c, linkedin=snapshot))
        return enriched
