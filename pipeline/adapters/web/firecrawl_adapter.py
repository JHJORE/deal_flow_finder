"""Firecrawl adapter for the ``WebFetcher`` port.

Verified against firecrawl-py 1.6.4:
- ``scrape_url`` returns the unwrapped ``data`` dict on success (it strips
  the ``{"success", "data"}`` envelope before returning).
- ``map_url`` returns the full envelope including ``links``.
- Both raise ``requests.exceptions.HTTPError`` on non-200 status; the
  message contains ``"Status code <n>"`` which is how we detect rate limits.
"""

from __future__ import annotations

import time
from typing import Any, Protocol

import requests

from pipeline.entities.errors import FetchError, ParseError, RateLimitError
from pipeline.entities.value_objects import Url


class _FirecrawlClient(Protocol):
    """Subset of the firecrawl-py client surface we depend on.

    Defined here so we can inject a fake in tests without importing the real
    SDK in test code.
    """

    def scrape_url(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]: ...

    def map_url(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]: ...


class FirecrawlWebFetcher:
    def __init__(self, client: _FirecrawlClient, *, backoff_seconds: float = 2.0) -> None:
        self._client = client
        self._backoff = backoff_seconds

    def fetch_markdown(self, url: Url) -> str:
        response = self._call(lambda: self._client.scrape_url(url.value, {"formats": ["markdown"]}))
        markdown = response.get("markdown")
        if not isinstance(markdown, str):
            raise ParseError(f"firecrawl returned no markdown for {url}: keys={list(response)}")
        return markdown

    def crawl_links_from(self, base_url: Url, link_selector_hint: str) -> list[Url]:
        params: dict[str, Any] = {"limit": 200}
        if link_selector_hint:
            params["search"] = link_selector_hint
        response = self._call(lambda: self._client.map_url(base_url.value, params))
        raw_links = response.get("links") or []
        out: list[Url] = []
        for raw in raw_links:
            if not isinstance(raw, str):
                continue
            try:
                out.append(Url(raw))
            except Exception:
                continue
        return out

    def _call(self, fn: Any) -> dict[str, Any]:
        try:
            response = fn()
        except requests.exceptions.HTTPError as exc:
            if _is_rate_limit(exc):
                time.sleep(self._backoff)
                try:
                    response = fn()
                except requests.exceptions.HTTPError as retry_exc:
                    if _is_rate_limit(retry_exc):
                        raise RateLimitError(
                            f"firecrawl rate limit persisted: {retry_exc}"
                        ) from retry_exc
                    raise FetchError(f"firecrawl http error on retry: {retry_exc}") from retry_exc
            else:
                raise FetchError(f"firecrawl http error: {exc}") from exc
        except Exception as exc:
            # The SDK also raises bare ``Exception`` for API-level failures
            # (e.g. ``response["success"] is False``). Treat as fetch errors.
            raise FetchError(f"firecrawl error: {exc}") from exc

        if not isinstance(response, dict):
            raise ParseError(f"unexpected firecrawl response type: {type(response).__name__}")
        return response


def _is_rate_limit(exc: requests.exceptions.HTTPError) -> bool:
    """SDK error messages format as 'Status code 429. ...'; also fall back to .response."""
    if "Status code 429" in str(exc):
        return True
    response = getattr(exc, "response", None)
    return response is not None and getattr(response, "status_code", None) == 429
