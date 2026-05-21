"""Andreessen Horowitz extractor.

The a16z site uses team cards with the partner name as a heading and a link
labelled with the partner name pointing to a personal profile. Portfolio
pages are stage-segmented (consumer, enterprise, crypto, etc.) but for
discovery we treat them uniformly.
"""

from __future__ import annotations

from typing import ClassVar

from pipeline.application.use_cases.firm_extractors.common import (
    absolutise,
    extract_links,
)
from pipeline.application.use_cases.firm_extractors.sequoia import (
    NON_COMPANY_LABELS,
    _handle_in,
    _linkedin_in,
    _looks_like_company_label,
    _section_chunks,
)
from pipeline.entities.models import BlogPost, Company, Partner, new_id
from pipeline.entities.value_objects import FirmName, Stage, Timestamp, Url


class A16zExtractor:
    firm: ClassVar[FirmName] = FirmName.A16Z

    def extract_partners(self, people_page_markdown: str, people_page_url: Url) -> list[Partner]:
        out: list[Partner] = []
        for level, name, body in _section_chunks(people_page_markdown):
            if level not in (2, 3):
                continue
            if (
                not name
                or len(name) > 80
                or name.lower()
                in {
                    "team",
                    "people",
                    "investing partners",
                }
            ):
                continue
            out.append(
                Partner(
                    id=new_id(),
                    name=name,
                    firm=self.firm,
                    role="General Partner",
                    x_handle=_handle_in(body),
                    linkedin_url=_linkedin_in(body),
                    blog_url=None,
                    bio="",
                )
            )
        return out

    def extract_companies(
        self, portfolio_page_markdown: str, portfolio_page_url: Url
    ) -> list[Company]:
        companies: list[Company] = []
        seen: set[str] = set()
        for link in extract_links(portfolio_page_markdown):
            label = link.label.strip()
            if not _looks_like_company_label(label):
                continue
            href = absolutise(link.href, portfolio_page_url)
            if href is None:
                continue
            if "a16z.com" in href.value and "/portfolio/" not in href.value:
                continue
            key = label.lower()
            if key in seen:
                continue
            seen.add(key)
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
        return companies

    def extract_blog_posts(
        self, blog_page_markdown: str, blog_page_url: Url, partners: list[Partner]
    ) -> list[BlogPost]:
        author_id = partners[0].id if partners else ""
        posts: list[BlogPost] = []
        for link in extract_links(blog_page_markdown):
            href = absolutise(link.href, blog_page_url)
            if href is None or "a16z.com" not in href.value:
                continue
            label = link.label.strip()
            if len(label) < 12 or label.lower() in NON_COMPANY_LABELS:
                continue
            posts.append(
                BlogPost(
                    id=new_id(),
                    author_partner_id=author_id,
                    title=label,
                    body="",
                    published_at=Timestamp.now(),
                    source_url=href,
                )
            )
        return posts
