"""Firm-specific extraction protocol.

Each firm's people / portfolio page has its own quirks. ``CrawlFirmSite``
delegates the parsing step to a per-firm implementer of this Protocol so the
use case stays firm-agnostic. To add a new firm, add a new implementation
here and register it in ``EXTRACTORS`` in :mod:`__init__`; no other layer
needs to change.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Protocol

from pipeline.entities.models import BlogPost, Company, Founder, Partner
from pipeline.entities.value_objects import FirmName, Url


@dataclass(frozen=True, slots=True)
class FirmSubgraph:
    """Everything a single firm contributes to the global graph."""

    firm: FirmName
    partners: tuple[Partner, ...]
    companies: tuple[Company, ...]
    founders: tuple[Founder, ...]
    blog_posts: tuple[BlogPost, ...]


class FirmExtractor(Protocol):
    """Parse a firm's markdown pages into a :class:`FirmSubgraph`."""

    firm: ClassVar[FirmName]

    def extract_partners(
        self, people_page_markdown: str, people_page_url: Url
    ) -> list[Partner]: ...

    def extract_companies(
        self, portfolio_page_markdown: str, portfolio_page_url: Url
    ) -> list[Company]: ...

    def extract_blog_posts(
        self, blog_page_markdown: str, blog_page_url: Url, partners: list[Partner]
    ) -> list[BlogPost]: ...
