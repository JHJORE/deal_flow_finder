"""Y Combinator extractor.

YC's "people" surface is the partner directory at /people; portfolio data
comes from the company directory at /companies. YC differs from
Sequoia/a16z in that *every* portfolio entry has a stable internal company
profile URL, which we keep as the canonical website pointer when no external
homepage is available.
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


class YCExtractor:
    firm: ClassVar[FirmName] = FirmName.YCOMBINATOR

    def extract_partners(self, people_page_markdown: str, people_page_url: Url) -> list[Partner]:
        partners: list[Partner] = []
        for level, name, body in _section_chunks(people_page_markdown):
            if level not in (2, 3, 4):
                continue
            if not name or len(name) > 80 or name.lower() in {"people", "partners", "team"}:
                continue
            partners.append(
                Partner(
                    id=new_id(),
                    name=name,
                    firm=self.firm,
                    role="Group Partner",
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
        out: list[Company] = []
        seen: set[str] = set()
        for link in extract_links(portfolio_page_markdown):
            label = link.label.strip()
            if not _looks_like_company_label(label):
                continue
            href = absolutise(link.href, portfolio_page_url)
            if href is None:
                continue
            # YC company pages look like /companies/<slug>.
            if "ycombinator.com" in href.value and "/companies/" not in href.value:
                continue
            key = label.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(
                Company(
                    id=new_id(),
                    name=label,
                    website=href,
                    sector=None,
                    stage=Stage.PRE_SEED,
                    invested_by=(self.firm,),
                    founder_ids=(),
                    description="",
                    linkedin_company_url=None,
                )
            )
        return out

    def extract_blog_posts(
        self, blog_page_markdown: str, blog_page_url: Url, partners: list[Partner]
    ) -> list[BlogPost]:
        author_id = partners[0].id if partners else ""
        out: list[BlogPost] = []
        for link in extract_links(blog_page_markdown):
            href = absolutise(link.href, blog_page_url)
            if href is None or "ycombinator.com" not in href.value:
                continue
            if "/blog/" not in href.value:
                continue
            label = link.label.strip()
            if len(label) < 12 or label.lower() in NON_COMPANY_LABELS:
                continue
            out.append(
                BlogPost(
                    id=new_id(),
                    author_partner_id=author_id,
                    title=label,
                    body="",
                    published_at=Timestamp.now(),
                    source_url=href,
                )
            )
        return out
