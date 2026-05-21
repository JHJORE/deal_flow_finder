"""Web fetching port.

Implementations live in ``adapters/web/``. The use case layer must never
import a scraper library — it only knows this Protocol.
"""

from __future__ import annotations

from typing import Protocol

from pipeline.entities.value_objects import Url


class WebFetcher(Protocol):
    def fetch_markdown(self, url: Url) -> str:
        """Fetch a URL and return its main content as markdown.

        Raises ``FetchError`` (or ``RateLimitError``) on network failure;
        raises ``ParseError`` if the response cannot be converted to markdown.
        """
        ...

    def crawl_links_from(self, base_url: Url, link_selector_hint: str) -> list[Url]:
        """Discover outbound links from ``base_url``.

        ``link_selector_hint`` is an adapter-interpreted hint (e.g. a CSS-like
        selector or a keyword the adapter knows how to map to its scraper).
        Returns the discovered links as ``Url`` values; deduplication is the
        adapter's job.
        """
        ...
