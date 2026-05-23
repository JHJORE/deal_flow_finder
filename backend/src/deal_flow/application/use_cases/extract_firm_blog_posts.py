from dataclasses import dataclass
from datetime import date
from urllib.parse import urljoin

from deal_flow.application.ports.services.web_extractor import WebExtractor
from deal_flow.domain.entities.blog_post import BlogPost


@dataclass(frozen=True)
class ExtractFirmBlogPostsInput:
    firm_domain: str
    limit: int = 10


class ExtractFirmBlogPosts:
    def __init__(self, extractor: WebExtractor) -> None:
        self._extractor = extractor

    def execute(self, input: ExtractFirmBlogPostsInput) -> list[BlogPost]:
        sections = self._extractor.discover_firm_sections(input.firm_domain)
        blog_url = sections.get("blog")
        if not blog_url:
            return []

        items = self._extractor.scrape_blog_posts(blog_url)[: input.limit]
        return [
            BlogPost(
                title=it.get("title") or "",
                url=urljoin(blog_url, it["url"]) if it.get("url") else "",
                author=it.get("author"),
                published_at=_parse_date(it.get("published_at")),
            )
            for it in items
        ]


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None
