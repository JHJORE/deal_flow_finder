"""Pull full essay text for partner blog URLs and persist as markdown files."""

from __future__ import annotations

from dataclasses import dataclass, replace

from pipeline.application.ports.repository import EntityRepository
from pipeline.application.ports.web import WebFetcher
from pipeline.entities.errors import DomainError
from pipeline.entities.models import BlogPost


@dataclass(frozen=True, slots=True)
class CollectBlogContent:
    web: WebFetcher
    repo: EntityRepository

    def execute(self, posts: list[BlogPost]) -> list[BlogPost]:
        out: list[BlogPost] = []
        for post in posts:
            try:
                body = self.web.fetch_markdown(post.source_url)
            except DomainError:
                continue
            filled = replace(post, body=body)
            self.repo.save(f"content/{post.id}", _serialise(filled))
            out.append(filled)
        return out


def _serialise(post: BlogPost) -> dict[str, object]:
    return {
        "id": post.id,
        "author_partner_id": post.author_partner_id,
        "title": post.title,
        "body": post.body,
        "published_at": post.published_at.iso(),
        "source_url": post.source_url.value,
    }
