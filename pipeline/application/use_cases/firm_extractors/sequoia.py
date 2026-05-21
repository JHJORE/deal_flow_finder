"""Sequoia Capital extractor.

Sequoia's people page uses a heading-per-partner layout; portfolio pages list
companies as cards with the company name as a heading and the website as a
following link. We accept that this is brittle — the test suite uses a
fixture markdown snapshot, and a real layout change will be caught there.
"""

from __future__ import annotations

import re
from typing import ClassVar

from pipeline.application.use_cases.firm_extractors.common import (
    absolutise,
    extract_links,
)
from pipeline.entities.models import BlogPost, Company, Partner, new_id
from pipeline.entities.value_objects import FirmName, Handle, Stage, Timestamp, Url

_X_RE = re.compile(r"https?://(?:www\.)?(?:twitter\.com|x\.com)/([A-Za-z0-9_]+)/?")
_LI_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9_\-%]+/?")
_HEADING_LINE_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)

# Reusable across siblings: noisy link labels we never want to treat as companies.
NON_COMPANY_LABELS = frozenset(
    {
        "home",
        "about",
        "team",
        "people",
        "careers",
        "contact",
        "press",
        "news",
        "blog",
        "podcast",
        "perspective",
        "perspectives",
        "twitter",
        "linkedin",
        "facebook",
        "instagram",
        "youtube",
        "github",
        "rss",
        "privacy",
        "terms",
        "subscribe",
        "menu",
        "search",
        "more",
        "next",
        "previous",
        "back",
        "read more",
        "learn more",
        "view all",
        "all companies",
        "all partners",
    }
)


class SequoiaExtractor:
    firm: ClassVar[FirmName] = FirmName.SEQUOIA

    def extract_partners(self, people_page_markdown: str, people_page_url: Url) -> list[Partner]:
        partners: list[Partner] = []
        for level, name, body in _section_chunks(people_page_markdown):
            if level not in (2, 3):
                continue
            if not name or len(name) > 80 or name.lower() in {"team", "people", "investors"}:
                continue
            partners.append(
                Partner(
                    id=new_id(),
                    name=name,
                    firm=self.firm,
                    role="Partner",
                    x_handle=_handle_in(body),
                    linkedin_url=_linkedin_in(body),
                    blog_url=None,
                    bio="",
                )
            )
        return partners

    def extract_companies(
        self, portfolio_page_markdown: str, portfolio_page_url: Url
    ) -> list[Company]:
        companies: list[Company] = []
        for link in extract_links(portfolio_page_markdown):
            label = link.label.strip()
            if not _looks_like_company_label(label):
                continue
            href = absolutise(link.href, portfolio_page_url)
            if href is None:
                continue
            # Sequoia portfolio pages link out to company websites and to
            # /companies/<slug> on their own site. Skip the internal ones.
            if "sequoiacap.com" in href.value and "/companies/" in href.value:
                continue
            companies.append(
                Company(
                    id=new_id(),
                    name=label,
                    website=href,
                    sector=None,
                    stage=Stage.UNKNOWN,
                    invested_by=(self.firm,),
                    founder_ids=(),
                    description="",
                    linkedin_company_url=None,
                )
            )
        return _dedupe_companies(companies)

    def extract_blog_posts(
        self, blog_page_markdown: str, blog_page_url: Url, partners: list[Partner]
    ) -> list[BlogPost]:
        # The blog page indexes essays — content extraction happens per-essay
        # in CollectBlogContent. Here we synthesise BlogPost stubs from links
        # whose label looks essay-shaped.
        author_id = partners[0].id if partners else ""
        posts: list[BlogPost] = []
        for link in extract_links(blog_page_markdown):
            href = absolutise(link.href, blog_page_url)
            if href is None or "sequoiacap.com" not in href.value:
                continue
            label = link.label.strip()
            if len(label) < 12 or label.lower() in NON_COMPANY_LABELS:
                continue
            posts.append(
                BlogPost(
                    id=new_id(),
                    author_partner_id=author_id,
                    title=label,
                    body="",  # filled by CollectBlogContent
                    published_at=Timestamp.now(),
                    source_url=href,
                )
            )
        return posts


# --------------------------------------------------------------------------- #
# Helpers (shared with sibling extractors via explicit import)
# --------------------------------------------------------------------------- #


def _section_chunks(markdown: str) -> list[tuple[int, str, str]]:
    """Split markdown into (heading_level, heading_text, body_until_next_heading) tuples.

    This is what makes per-partner handle scoping work: each Partner gets
    only the markdown between their heading and the next, so a Twitter URL
    sitting under "Roelof Botha" doesn't get assigned to "Alfred Lin" below.
    """
    matches = list(_HEADING_LINE_RE.finditer(markdown))
    chunks: list[tuple[int, str, str]] = []
    for i, m in enumerate(matches):
        level = len(m.group(1))
        text = m.group(2).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        chunks.append((level, text, markdown[body_start:body_end]))
    return chunks


def _handle_in(text: str) -> Handle | None:
    match = _X_RE.search(text)
    return Handle(match.group(1)) if match else None


def _linkedin_in(text: str) -> Url | None:
    match = _LI_RE.search(text)
    return Url(match.group(0)) if match else None


def _looks_like_company_label(label: str) -> bool:
    if not label or len(label) > 80 or len(label) < 2:
        return False
    return label.lower() not in NON_COMPANY_LABELS


def _dedupe_companies(companies: list[Company]) -> list[Company]:
    seen: set[str] = set()
    out: list[Company] = []
    for c in companies:
        key = c.name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


__all__ = ["SequoiaExtractor"]
