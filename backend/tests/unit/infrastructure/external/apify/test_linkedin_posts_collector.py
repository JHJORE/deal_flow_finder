import json

import httpx
import pytest

from deal_flow.infrastructure.external.apify.linkedin_posts_collector import (
    ApifyRunError,
    HarvestApiLinkedInCollector,
)


def _build(tmp_path, handler, refresh: bool = False) -> HarvestApiLinkedInCollector:
    c = HarvestApiLinkedInCollector(
        api_token="t",
        actor_id="harvestapi~linkedin-profile-posts",
        cache_dir=tmp_path,
        refresh=refresh,
    )
    c._client = httpx.Client(
        base_url=c.BASE_URL,
        headers={"Authorization": "Bearer t"},
        transport=httpx.MockTransport(handler),
    )
    return c


def test_sends_actor_input_and_groups_response_by_input_url(tmp_path):
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            json=[
                {"id": "1", "inputUrl": "https://linkedin.com/in/alice"},
                {"id": "2", "inputUrl": "https://linkedin.com/in/alice"},
                {"id": "3", "inputUrl": "https://linkedin.com/in/bob"},
            ],
        )

    out = _build(tmp_path, handler).fetch_posts(
        ["https://linkedin.com/in/alice", "https://linkedin.com/in/bob"],
        max_posts=10,
        include_reactions=True,
        posted_limit="month",
    )

    req = captured[0]
    assert req.url.path == (
        "/v2/acts/harvestapi~linkedin-profile-posts/run-sync-get-dataset-items"
    )
    assert req.headers["authorization"] == "Bearer t"
    body = json.loads(req.content)
    assert body["targetUrls"] == [
        "https://linkedin.com/in/alice",
        "https://linkedin.com/in/bob",
    ]
    assert body["maxPosts"] == 10
    assert body["scrapeReactions"] is True
    assert body["postedLimit"] == "month"

    assert [p["id"] for p in out["https://linkedin.com/in/alice"]] == ["1", "2"]
    assert [p["id"] for p in out["https://linkedin.com/in/bob"]] == ["3"]


def test_second_call_only_sends_misses(tmp_path):
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        body = json.loads(request.content)
        return httpx.Response(
            200, json=[{"id": f"id-{u}", "inputUrl": u} for u in body["targetUrls"]]
        )

    c = _build(tmp_path, handler)
    c.fetch_posts(["https://linkedin.com/in/alice"], max_posts=5)
    c.fetch_posts(
        ["https://linkedin.com/in/alice", "https://linkedin.com/in/bob"], max_posts=5
    )

    assert len(captured) == 2
    assert json.loads(captured[1].content)["targetUrls"] == ["https://linkedin.com/in/bob"]


def test_refresh_bypasses_cache(tmp_path):
    n = {"calls": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        n["calls"] += 1
        return httpx.Response(
            200, json=[{"id": "x", "inputUrl": "https://linkedin.com/in/foo"}]
        )

    _build(tmp_path, handler).fetch_posts(["https://linkedin.com/in/foo"], max_posts=5)
    _build(tmp_path, handler, refresh=True).fetch_posts(
        ["https://linkedin.com/in/foo"], max_posts=5
    )
    assert n["calls"] == 2


def test_raises_apify_run_error_on_non_2xx(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="rate limited")

    with pytest.raises(ApifyRunError, match="429"):
        _build(tmp_path, handler).fetch_posts(
            ["https://linkedin.com/in/foo"], max_posts=5
        )
