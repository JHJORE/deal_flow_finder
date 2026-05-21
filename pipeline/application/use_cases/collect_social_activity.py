"""Collect posts, likes, replies, and follower snapshots for a set of handles.

Persistence model: one JSON file per handle under ``data/social/<handle>.json``,
plus a top-level ``data/social/snapshots.json`` aggregating the snapshots so
the signal layer can compare current vs prior periods cheaply.

Partial-write checkpointing: each handle is persisted as soon as it is
fetched, so a rate-limit failure mid-run leaves the work-to-date intact.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from pipeline.application.ports.repository import EntityRepository
from pipeline.application.ports.social import SocialFetcher
from pipeline.entities.errors import DomainError, RateLimitError
from pipeline.entities.models import Engagement, Post, SocialSnapshot
from pipeline.entities.value_objects import Handle, Timestamp


@dataclass(frozen=True, slots=True)
class HandleActivity:
    handle: Handle
    snapshot: SocialSnapshot | None
    posts: tuple[Post, ...]
    likes: tuple[Engagement, ...]
    replies: tuple[Engagement, ...]


@dataclass(frozen=True, slots=True)
class CollectSocialActivity:
    social: SocialFetcher
    repo: EntityRepository

    def execute(
        self,
        handles: list[Handle],
        lookback_days: int = 30,
    ) -> list[HandleActivity]:
        since = Timestamp(Timestamp.now().value - timedelta(days=lookback_days))
        results: list[HandleActivity] = []
        snapshots: list[dict[str, Any]] = []

        for handle in handles:
            try:
                activity = self._collect_one(handle, since)
            except RateLimitError:
                # Stop the loop: the remote service has asked us to slow down.
                # Already-collected handles are persisted; the rest stay queued.
                break
            except DomainError:
                continue

            self.repo.save(f"social/{handle.value}", _serialise(activity))
            if activity.snapshot is not None:
                snapshots.append(_serialise_snapshot(activity.snapshot))
            results.append(activity)

        self.repo.save("social/snapshots", {"snapshots": snapshots})
        return results

    def _collect_one(self, handle: Handle, since: Timestamp) -> HandleActivity:
        snapshot = self.social.fetch_user(handle)
        posts = tuple(self.social.fetch_recent_posts(handle, since))
        likes = tuple(self.social.fetch_recent_likes(handle, since))
        replies = tuple(self.social.fetch_recent_replies(handle, since))
        return HandleActivity(
            handle=handle, snapshot=snapshot, posts=posts, likes=likes, replies=replies
        )


def _serialise(activity: HandleActivity) -> dict[str, Any]:
    return {
        "handle": activity.handle.value,
        "snapshot": _serialise_snapshot(activity.snapshot) if activity.snapshot else None,
        "posts": [_serialise_post(p) for p in activity.posts],
        "likes": [_serialise_engagement(e) for e in activity.likes],
        "replies": [_serialise_engagement(e) for e in activity.replies],
    }


def _serialise_snapshot(s: SocialSnapshot) -> dict[str, Any]:
    return {
        "handle": s.handle.value,
        "captured_at": s.captured_at.iso(),
        "follower_count": s.follower_count,
        "following_count": s.following_count,
        "post_count_30d": s.post_count_30d,
        "post_count_prior_30d": s.post_count_prior_30d,
    }


def _serialise_post(p: Post) -> dict[str, Any]:
    return {
        "id": p.id,
        "author_handle": p.author_handle.value,
        "text": p.text,
        "timestamp": p.timestamp.iso(),
        "url": p.url.value,
        "like_count": p.like_count,
        "reply_count": p.reply_count,
        "repost_count": p.repost_count,
    }


def _serialise_engagement(e: Engagement) -> dict[str, Any]:
    return {
        "id": e.id,
        "actor_handle": e.actor_handle.value,
        "target_handle": e.target_handle.value,
        "kind": e.kind.value,
        "timestamp": e.timestamp.iso(),
        "target_post_id": e.target_post_id,
        "context": e.context,
    }
