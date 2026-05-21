"""Shared markdown parsing helpers for firm extractors.

These are intentionally simple. The extractors run over Firecrawl-produced
markdown, which is already cleaned-up text, so we don't try to be a generic
HTML parser. If a firm changes its layout we expect the extractor to need
manual updates — and the test suite to catch it via a fixture file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.entities.value_objects import Url

# Capture standard markdown links: [label](href). We deliberately do not
# follow image links (![]) or reference-style links.
_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)")


@dataclass(frozen=True, slots=True)
class MarkdownLink:
    label: str
    href: str


def extract_links(markdown: str) -> list[MarkdownLink]:
    return [
        MarkdownLink(label=m.group(1).strip(), href=m.group(2).strip())
        for m in _LINK_RE.finditer(markdown)
    ]


def absolutise(href: str, base: Url) -> Url | None:
    """Turn a possibly relative href into an absolute :class:`Url`. Returns ``None`` on failure."""
    if href.startswith("http://") or href.startswith("https://"):
        try:
            return Url(href)
        except Exception:
            return None
    if href.startswith("//"):
        try:
            scheme = base.value.split("://", 1)[0]
            return Url(f"{scheme}:{href}")
        except Exception:
            return None
    if href.startswith("/"):
        try:
            scheme, rest = base.value.split("://", 1)
            root = rest.split("/", 1)[0]
            return Url(f"{scheme}://{root}{href}")
        except Exception:
            return None
    # Drop fragments and obvious mailtos.
    if href.startswith("#") or href.startswith("mailto:"):
        return None
    try:
        return Url(base.value.rstrip("/") + "/" + href)
    except Exception:
        return None
