from dataclasses import dataclass, replace
from datetime import UTC, datetime
from urllib.parse import urlparse

from deal_flow.application.ports.repositories.partner_directory import PartnerDirectory
from deal_flow.application.ports.services.linkedin_collector import LinkedInCollector
from deal_flow.application.use_cases.linkedin_post_mapping import to_snapshot
from deal_flow.domain.entities.partner import Partner

_LINKEDIN_HOSTS = {
    "linkedin.com",
    "www.linkedin.com",
    "linkedin.cn",
    "www.linkedin.cn",
}


def handle_from_linkedin_url(linkedin_url: str | None) -> str | None:
    """Pull the slug out of a LinkedIn ``/in/<slug>`` profile URL.

    Returns the lower-cased slug or ``None`` if the URL doesn't look like a
    personal profile. Exposed so the route can match a URL-supplied handle
    against directory partners without re-parsing.
    """
    if not linkedin_url:
        return None
    parsed = urlparse(linkedin_url.strip())
    host = (parsed.netloc or "").lower()
    if host not in _LINKEDIN_HOSTS:
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2 or parts[0].lower() != "in":
        return None
    return parts[1].lower()


@dataclass(frozen=True)
class EnrichFirmPartnersWithLinkedInInput:
    firm_domain: str
    max_posts: int = 20
    include_reactions: bool = False
    include_comments: bool = False
    max_reactions: int = 5
    max_comments: int = 5
    posted_limit: str | None = None
    # If set, only the partner whose linkedin_url slug equals this handle is
    # enriched (and the result list contains just that one). Lets the
    # single-handle route reuse this use case without scraping the whole
    # roster.
    target_handle: str | None = None


class EnrichFirmPartnersWithLinkedIn:
    """Load a firm's partner roster from the directory and attach LinkedIn
    activity to each partner that has a ``linkedin_url``.

    One collector call covers every URL in one upstream actor run (the
    adapter handles per-URL caching, so partial re-runs only pay for the
    misses). Partners without a LinkedIn URL pass through unchanged.
    """

    def __init__(
        self,
        directory: PartnerDirectory,
        collector: LinkedInCollector,
    ) -> None:
        self._directory = directory
        self._collector = collector

    def execute(self, input: EnrichFirmPartnersWithLinkedInInput) -> list[Partner]:
        partners = self._directory.list_partners(input.firm_domain)
        if input.target_handle:
            needle = input.target_handle.lower().lstrip("@")
            partners = [
                p for p in partners
                if handle_from_linkedin_url(p.linkedin_url) == needle
            ]
        urls = [p.linkedin_url for p in partners if p.linkedin_url]
        if not urls:
            return partners

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

        enriched: list[Partner] = []
        for p in partners:
            if not p.linkedin_url or p.linkedin_url not in posts_by_url:
                enriched.append(p)
                continue
            snapshot = to_snapshot(
                p.linkedin_url, posts_by_url[p.linkedin_url], collected_at=now
            )
            enriched.append(replace(p, linkedin=snapshot))
        return enriched
