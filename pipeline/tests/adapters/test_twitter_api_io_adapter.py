from __future__ import annotations

import httpx
import respx

from pipeline.adapters.social.twitter_api_io_adapter import (
    BASE_URL,
    TwitterApiIoSocialFetcher,
)
from pipeline.entities.value_objects import Handle, Timestamp


def _fetcher() -> TwitterApiIoSocialFetcher:
    return TwitterApiIoSocialFetcher(httpx.Client())


@respx.mock
def test_fetch_user_returns_snapshot() -> None:
    respx.get(f"{BASE_URL}/twitter/user/info").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "followers": 12345,
                    "following": 200,
                    "posts_30d": 8,
                    "posts_prior_30d": 3,
                }
            },
        )
    )
    snapshot = _fetcher().fetch_user(Handle("roelofbotha"))
    assert snapshot is not None
    assert snapshot.follower_count == 12345
    assert snapshot.post_count_30d == 8


@respx.mock
def test_fetch_user_404_returns_none() -> None:
    respx.get(f"{BASE_URL}/twitter/user/info").mock(return_value=httpx.Response(404))
    assert _fetcher().fetch_user(Handle("ghost")) is None


@respx.mock
def test_fetch_recent_posts_parses_items() -> None:
    respx.get(f"{BASE_URL}/twitter/user/last_tweets").mock(
        return_value=httpx.Response(
            200,
            json={
                "tweets": [
                    {
                        "id": "1",
                        "text": "hello",
                        "createdAt": "2024-01-01T00:00:00Z",
                        "url": "https://x.com/roelofbotha/status/1",
                        "likeCount": 10,
                        "replyCount": 1,
                        "retweetCount": 2,
                    },
                    {"id": "bad"},  # missing fields; must be skipped, not crash.
                ]
            },
        )
    )
    posts = _fetcher().fetch_recent_posts(Handle("roelofbotha"), Timestamp.now())
    assert len(posts) == 1
    assert posts[0].text == "hello"
    assert posts[0].like_count == 10
