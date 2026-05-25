from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from deal_flow.domain.entities.linkedin.linkedin_comment import LinkedInComment
from deal_flow.domain.entities.linkedin.linkedin_reaction import LinkedInReaction


@dataclass(frozen=True)
class LinkedInPost:
    id: str
    url: str | None = None
    text: str | None = None
    posted_at: datetime | None = None
    author_name: str | None = None
    author_url: str | None = None
    media_urls: tuple[str, ...] = field(default_factory=tuple)
    reactions_count: int | None = None
    comments_count: int | None = None
    reposts_count: int | None = None
    reposted_post: LinkedInPost | None = None
    quoted_post: LinkedInPost | None = None
    reactions: tuple[LinkedInReaction, ...] = field(default_factory=tuple)
    comments: tuple[LinkedInComment, ...] = field(default_factory=tuple)

    @property
    def is_repost(self) -> bool:
        return self.reposted_post is not None

    @property
    def is_quote(self) -> bool:
        return self.quoted_post is not None
