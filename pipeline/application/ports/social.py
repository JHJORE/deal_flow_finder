"""Social activity port (X / Twitter)."""

from __future__ import annotations

from typing import Protocol

from pipeline.entities.models import Engagement, Post, SocialSnapshot
from pipeline.entities.value_objects import Handle, Timestamp


class SocialFetcher(Protocol):
    def fetch_user(self, handle: Handle) -> SocialSnapshot | None:
        """Return a follower/post-volume snapshot, or ``None`` if the handle is missing."""
        ...

    def fetch_recent_posts(self, handle: Handle, since: Timestamp) -> list[Post]: ...

    def fetch_recent_likes(self, handle: Handle, since: Timestamp) -> list[Engagement]: ...

    def fetch_recent_replies(self, handle: Handle, since: Timestamp) -> list[Engagement]: ...

    def fetch_following(self, handle: Handle, limit: int) -> list[Handle]: ...
