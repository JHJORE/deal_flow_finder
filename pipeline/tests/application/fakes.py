"""In-memory test doubles for ports. Used by every use-case test."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from pipeline.entities.errors import FetchError, RateLimitError
from pipeline.entities.models import (
    Engagement,
    Filing,
    LinkedInCompany,
    LinkedInProfile,
    Post,
    SocialSnapshot,
)
from pipeline.entities.value_objects import Handle, Timestamp, Url


@dataclass
class FakeWebFetcher:
    pages: dict[str, str] = field(default_factory=dict)
    fail_urls: set[str] = field(default_factory=set)

    def fetch_markdown(self, url: Url) -> str:
        if url.value in self.fail_urls:
            raise FetchError(f"fake fetch failed for {url}")
        return self.pages.get(url.value, "")

    def crawl_links_from(self, base_url: Url, link_selector_hint: str) -> list[Url]:
        return []


@dataclass
class FakeSocialFetcher:
    snapshots: dict[str, SocialSnapshot] = field(default_factory=dict)
    posts_by_handle: dict[str, list[Post]] = field(default_factory=lambda: defaultdict(list))
    likes_by_handle: dict[str, list[Engagement]] = field(default_factory=lambda: defaultdict(list))
    replies_by_handle: dict[str, list[Engagement]] = field(
        default_factory=lambda: defaultdict(list)
    )
    rate_limit_after: int | None = None
    _calls: int = 0

    def fetch_user(self, handle: Handle) -> SocialSnapshot | None:
        self._tick()
        return self.snapshots.get(handle.value)

    def fetch_recent_posts(self, handle: Handle, since: Timestamp) -> list[Post]:
        self._tick()
        return list(self.posts_by_handle.get(handle.value, []))

    def fetch_recent_likes(self, handle: Handle, since: Timestamp) -> list[Engagement]:
        self._tick()
        return list(self.likes_by_handle.get(handle.value, []))

    def fetch_recent_replies(self, handle: Handle, since: Timestamp) -> list[Engagement]:
        self._tick()
        return list(self.replies_by_handle.get(handle.value, []))

    def fetch_following(self, handle: Handle, limit: int) -> list[Handle]:
        return []

    def _tick(self) -> None:
        self._calls += 1
        if self.rate_limit_after is not None and self._calls > self.rate_limit_after:
            raise RateLimitError("fake rate limit")


@dataclass
class FakeLinkedInFetcher:
    profiles: dict[str, LinkedInProfile] = field(default_factory=dict)
    companies: dict[str, LinkedInCompany] = field(default_factory=dict)

    def fetch_profile(self, linkedin_url: Url) -> LinkedInProfile | None:
        return self.profiles.get(linkedin_url.value)

    def fetch_company(self, linkedin_url: Url) -> LinkedInCompany | None:
        return self.companies.get(linkedin_url.value)


@dataclass
class FakeFilingFetcher:
    filings_by_alias: dict[str, list[Filing]] = field(default_factory=dict)

    def search_form_d(self, investor_alias: str, since: Timestamp) -> list[Filing]:
        return list(self.filings_by_alias.get(investor_alias, []))


@dataclass
class FakeRepository:
    store: dict[str, Any] = field(default_factory=dict)

    def save(self, key: str, value: Any) -> None:
        self.store[key] = value

    def load(self, key: str) -> Any | None:
        return self.store.get(key)

    def list_keys(self, prefix: str) -> list[str]:
        return sorted(k for k in self.store if k.startswith(prefix))
