from __future__ import annotations

from typing import Any

import pytest
import requests

from pipeline.adapters.web.firecrawl_adapter import FirecrawlWebFetcher
from pipeline.entities.errors import FetchError, ParseError, RateLimitError
from pipeline.entities.value_objects import Url


def _http_error(status: int, message: str) -> requests.exceptions.HTTPError:
    """Mirror the shape firecrawl-py raises: HTTPError with a status-coded message."""
    response = requests.models.Response()
    response.status_code = status
    return requests.exceptions.HTTPError(message, response=response)


class FakeFirecrawl:
    def __init__(
        self, scrape: dict[str, Any] | None = None, raises: Exception | None = None
    ) -> None:
        self._scrape: dict[str, Any] = scrape if scrape is not None else {}
        self._raises = raises
        self.calls = 0

    def scrape_url(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls += 1
        if self._raises is not None:
            raise self._raises
        return self._scrape

    def map_url(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return {"success": True, "links": ["https://stripe.com", "javascript:void"]}


def test_returns_markdown() -> None:
    adapter = FirecrawlWebFetcher(FakeFirecrawl(scrape={"markdown": "# Hi"}))
    assert adapter.fetch_markdown(Url("https://example.com")) == "# Hi"


def test_no_markdown_raises_parse_error() -> None:
    adapter = FirecrawlWebFetcher(FakeFirecrawl(scrape={}))
    with pytest.raises(ParseError):
        adapter.fetch_markdown(Url("https://example.com"))


def test_generic_error_becomes_fetch_error() -> None:
    adapter = FirecrawlWebFetcher(FakeFirecrawl(raises=RuntimeError("boom")))
    with pytest.raises(FetchError):
        adapter.fetch_markdown(Url("https://example.com"))


def test_non_429_http_error_becomes_fetch_error_without_retry() -> None:
    fake = FakeFirecrawl(raises=_http_error(500, "Internal Server Error: Status code 500"))
    adapter = FirecrawlWebFetcher(fake, backoff_seconds=0)
    with pytest.raises(FetchError):
        adapter.fetch_markdown(Url("https://example.com"))
    assert fake.calls == 1


def test_persistent_429_raises_rate_limit_error_after_one_retry() -> None:
    fake = FakeFirecrawl(
        raises=_http_error(429, "Unexpected error during scrape URL: Status code 429")
    )
    adapter = FirecrawlWebFetcher(fake, backoff_seconds=0)
    with pytest.raises(RateLimitError):
        adapter.fetch_markdown(Url("https://example.com"))
    # One initial attempt + one retry.
    assert fake.calls == 2


def test_map_url_returns_valid_urls_only() -> None:
    adapter = FirecrawlWebFetcher(FakeFirecrawl(scrape={}))
    links = adapter.crawl_links_from(Url("https://example.com"), "")
    assert [u.value for u in links] == ["https://stripe.com"]
