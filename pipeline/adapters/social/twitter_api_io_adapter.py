"""twitterapi.io adapter for the ``SocialFetcher`` port.

twitterapi.io is a third-party gateway over X/Twitter data. We hit it with
plain ``httpx`` rather than a vendor SDK to keep the dependency surface small.
Endpoint paths here track its public docs (https://docs.twitterapi.io); we
defensively coerce every field to the domain types and skip records that
fail validation rather than failing the whole batch.
"""

from __future__ import annotations

from typing import Any

import httpx

from pipeline.adapters._common.http import request_with_retry
from pipeline.entities.errors import ParseError, ValidationError
from pipeline.entities.models import Engagement, Post, SocialSnapshot, new_id
from pipeline.entities.value_objects import EngagementType, Handle, Timestamp, Url

BASE_URL = "https://api.twitterapi.io"


class TwitterApiIoSocialFetcher:
    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    # ------------------------------------------------------------------ #
    # User snapshot
    # ------------------------------------------------------------------ #
    def fetch_user(self, handle: Handle) -> SocialSnapshot | None:
        resp = request_with_retry(
            lambda: self._client.get(
                f"{BASE_URL}/twitter/user/info", params={"userName": handle.value}
            )
        )
        if resp.status_code == 404:
            return None
        payload = _json(resp)
        user = payload.get("data") or payload.get("user") or payload
        if not user:
            return None
        try:
            return SocialSnapshot(
                handle=handle,
                captured_at=Timestamp.now(),
                follower_count=int(user.get("followers", user.get("followersCount", 0))),
                following_count=int(user.get("following", user.get("followingCount", 0))),
                post_count_30d=int(user.get("posts_30d", 0)),
                post_count_prior_30d=int(user.get("posts_prior_30d", 0)),
            )
        except (TypeError, ValueError, ValidationError) as exc:
            raise ParseError(f"could not parse user payload for {handle}: {exc}") from exc

    # ------------------------------------------------------------------ #
    # Activity
    # ------------------------------------------------------------------ #
    def fetch_recent_posts(self, handle: Handle, since: Timestamp) -> list[Post]:
        resp = request_with_retry(
            lambda: self._client.get(
                f"{BASE_URL}/twitter/user/last_tweets",
                params={"userName": handle.value, "since": since.iso()},
            )
        )
        if resp.status_code == 404:
            return []
        items = _items(_json(resp), ("tweets", "data", "items"))
        out: list[Post] = []
        for raw in items:
            post = _to_post(raw, handle)
            if post is not None:
                out.append(post)
        return out

    def fetch_recent_likes(self, handle: Handle, since: Timestamp) -> list[Engagement]:
        resp = request_with_retry(
            lambda: self._client.get(
                f"{BASE_URL}/twitter/user/likes",
                params={"userName": handle.value, "since": since.iso()},
            )
        )
        if resp.status_code == 404:
            return []
        return _to_engagements(_items(_json(resp), ("likes", "data")), handle, EngagementType.LIKE)

    def fetch_recent_replies(self, handle: Handle, since: Timestamp) -> list[Engagement]:
        resp = request_with_retry(
            lambda: self._client.get(
                f"{BASE_URL}/twitter/user/replies",
                params={"userName": handle.value, "since": since.iso()},
            )
        )
        if resp.status_code == 404:
            return []
        return _to_engagements(
            _items(_json(resp), ("replies", "data")), handle, EngagementType.REPLY
        )

    def fetch_following(self, handle: Handle, limit: int) -> list[Handle]:
        resp = request_with_retry(
            lambda: self._client.get(
                f"{BASE_URL}/twitter/user/following",
                params={"userName": handle.value, "limit": limit},
            )
        )
        if resp.status_code == 404:
            return []
        out: list[Handle] = []
        for raw in _items(_json(resp), ("following", "data")):
            name = raw.get("userName") or raw.get("username") or raw.get("screen_name")
            if not name:
                continue
            try:
                out.append(Handle(name))
            except ValidationError:
                continue
        return out


# ---------------------------------------------------------------------- #
# Internal parsing helpers
# ---------------------------------------------------------------------- #


def _json(resp: httpx.Response) -> dict[str, Any]:
    try:
        payload = resp.json()
    except ValueError as exc:
        raise ParseError(f"twitterapi.io returned non-json: {exc}") from exc
    if not isinstance(payload, dict):
        raise ParseError(f"twitterapi.io returned non-object: {type(payload).__name__}")
    return payload


def _items(payload: dict[str, Any], candidates: tuple[str, ...]) -> list[dict[str, Any]]:
    for key in candidates:
        value = payload.get(key)
        if isinstance(value, list):
            return [v for v in value if isinstance(v, dict)]
    return []


def _to_post(raw: dict[str, Any], author: Handle) -> Post | None:
    try:
        ts = Timestamp.from_iso(raw.get("createdAt") or raw.get("created_at") or "")
        url = Url(raw.get("url") or f"https://x.com/{author.value}/status/{raw.get('id')}")
        return Post(
            id=str(raw.get("id") or new_id()),
            author_handle=author,
            text=str(raw.get("text", "")),
            timestamp=ts,
            url=url,
            like_count=int(raw.get("likeCount", raw.get("favorite_count", 0))),
            reply_count=int(raw.get("replyCount", raw.get("reply_count", 0))),
            repost_count=int(raw.get("retweetCount", raw.get("retweet_count", 0))),
        )
    except (TypeError, ValueError, ValidationError):
        return None


def _to_engagements(
    items: list[dict[str, Any]], actor: Handle, kind: EngagementType
) -> list[Engagement]:
    out: list[Engagement] = []
    for raw in items:
        target_name = raw.get("targetUserName") or raw.get("userName") or raw.get("screen_name")
        if not target_name:
            continue
        try:
            ts = Timestamp.from_iso(raw.get("createdAt") or raw.get("created_at") or "")
            target = Handle(target_name)
        except (ValueError, ValidationError):
            continue
        out.append(
            Engagement(
                id=str(raw.get("id") or new_id()),
                actor_handle=actor,
                target_handle=target,
                kind=kind,
                timestamp=ts,
                target_post_id=str(raw.get("targetId")) if raw.get("targetId") else None,
                context=str(raw.get("text", "")),
            )
        )
    return out
