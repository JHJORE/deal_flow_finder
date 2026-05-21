from __future__ import annotations

from pipeline.application.use_cases.collect_social_activity import CollectSocialActivity
from pipeline.entities.models import Post, SocialSnapshot, new_id
from pipeline.entities.value_objects import Handle, Timestamp, Url
from pipeline.tests.application.fakes import FakeRepository, FakeSocialFetcher


def _snapshot(handle: str) -> SocialSnapshot:
    return SocialSnapshot(
        handle=Handle(handle),
        captured_at=Timestamp.now(),
        follower_count=10_000,
        following_count=500,
        post_count_30d=20,
        post_count_prior_30d=5,
    )


def _post(handle: str) -> Post:
    return Post(
        id=new_id(),
        author_handle=Handle(handle),
        text="hello",
        timestamp=Timestamp.now(),
        url=Url(f"https://x.com/{handle}/status/1"),
        like_count=10,
        reply_count=1,
        repost_count=2,
    )


def test_persists_per_handle_and_aggregate_snapshots() -> None:
    fetcher = FakeSocialFetcher(
        snapshots={"alice": _snapshot("alice"), "bob": _snapshot("bob")},
        posts_by_handle={"alice": [_post("alice")]},
    )
    repo = FakeRepository()
    out = CollectSocialActivity(social=fetcher, repo=repo).execute([Handle("alice"), Handle("bob")])
    assert len(out) == 2
    assert "social/alice" in repo.store
    assert "social/bob" in repo.store
    assert len(repo.store["social/snapshots"]["snapshots"]) == 2


def test_rate_limit_short_circuits_but_keeps_prior_writes() -> None:
    fetcher = FakeSocialFetcher(
        snapshots={"alice": _snapshot("alice"), "bob": _snapshot("bob")},
        rate_limit_after=4,  # alice (4 fetches) succeeds; bob trips the limit.
    )
    repo = FakeRepository()
    out = CollectSocialActivity(social=fetcher, repo=repo).execute([Handle("alice"), Handle("bob")])
    assert len(out) == 1
    assert "social/alice" in repo.store
    assert "social/bob" not in repo.store
