"""Map raw post dicts from a ``LinkedInCollector`` into domain entities.

Shared by ``EnrichFirmPartnersWithLinkedIn`` and
``EnrichPortfolioCompaniesWithLinkedIn``. Field names track harvestapi's
output verbatim — if the actor renames a field we'll see it fail in tests
or on first live call, and fix in one place.
"""

from __future__ import annotations

from datetime import UTC, datetime

from deal_flow.domain.entities.linkedin.linkedin_comment import LinkedInComment
from deal_flow.domain.entities.linkedin.linkedin_post import LinkedInPost
from deal_flow.domain.entities.linkedin.linkedin_reaction import LinkedInReaction
from deal_flow.domain.entities.linkedin.linkedin_snapshot import LinkedInSnapshot


def to_snapshot(
    profile_url: str,
    raw_posts: list[dict],
    *,
    collected_at: datetime | None = None,
) -> LinkedInSnapshot:
    posts = tuple(_to_post(p) for p in raw_posts)
    return LinkedInSnapshot(
        profile_url=profile_url,
        collected_at=collected_at or datetime.now(UTC),
        posts=posts,
        reposts=tuple(p for p in posts if p.is_repost),
        quote_posts=tuple(p for p in posts if p.is_quote),
    )


def _to_post(raw: dict) -> LinkedInPost:
    author = raw.get("author") or {}
    reposted = raw.get("repostedPost")
    quoted = raw.get("quotedPost")
    return LinkedInPost(
        id=raw.get("id") or "",
        url=raw.get("postUrl"),
        text=raw.get("text"),
        posted_at=_parse_dt(raw.get("postedAt")),
        author_name=author.get("name"),
        author_url=author.get("linkedinUrl"),
        media_urls=tuple(m.get("url") for m in raw.get("media") or [] if m.get("url")),
        reactions_count=raw.get("reactionsCount"),
        comments_count=raw.get("commentsCount"),
        reposts_count=raw.get("repostsCount"),
        reposted_post=_to_post(reposted) if reposted else None,
        quoted_post=_to_post(quoted) if quoted else None,
        reactions=tuple(_to_reaction(r) for r in raw.get("reactions") or []),
        comments=tuple(_to_comment(c) for c in raw.get("comments") or []),
    )


def _to_reaction(raw: dict) -> LinkedInReaction:
    actor = raw.get("actor") or {}
    return LinkedInReaction(
        reaction_type=raw.get("reactionType"),
        actor_name=actor.get("name"),
        actor_url=actor.get("linkedinUrl"),
        actor_headline=actor.get("headline"),
    )


def _to_comment(raw: dict) -> LinkedInComment:
    author = raw.get("author") or {}
    return LinkedInComment(
        text=raw.get("text") or "",
        author_name=author.get("name"),
        author_url=author.get("linkedinUrl"),
        author_headline=author.get("headline"),
        posted_at=_parse_dt(raw.get("postedAt")),
        like_count=raw.get("likeCount"),
    )


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
