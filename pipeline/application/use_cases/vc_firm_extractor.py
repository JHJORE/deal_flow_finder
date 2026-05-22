"""Generic two-stage VC firm extractor backed by Firecrawl v2 JSON mode.

For any firm — given its team, portfolio, and blog listing URLs — this use case
produces three lists of plain dicts:

* ``extract_team`` — partners with bios, socials, education, experience.
* ``extract_portfolio`` — companies with sectors, websites, founders.
* ``extract_blog`` — recent posts with title/url/author/date.

Team and portfolio are two-stage (listing → batch detail enrichment). Blog is
single-stage. The cap of 10 records per category lives in the prompts and in
the slicing here — never in the Pydantic schemas (per Firecrawl docs, JSON
Schema ``maxItems`` makes the LLM hallucinate filler entries).

Per-firm logic is forbidden in this file. The class sees URLs in and dicts out.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urljoin

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Web port (structured JSON mode)
# --------------------------------------------------------------------------- #


class StructuredWebFetcher(Protocol):
    """Subset of ``FirecrawlWebFetcher`` the use case depends on."""

    def fetch_structured(
        self, url: str, schema_cls: type[BaseModel], prompt: str
    ) -> dict[str, Any]: ...

    def fetch_structured_batch(
        self, urls: list[str], schema_cls: type[BaseModel], prompt: str
    ) -> list[dict[str, Any]]: ...


# --------------------------------------------------------------------------- #
# Schemas — flat, no maxItems/minItems, every Optional defaults to None.
# --------------------------------------------------------------------------- #


# ─── Team, stage 1 (listing page) ───


class PartnerListing(BaseModel):
    name: str = Field(description="Partner's full name.")
    role: str | None = Field(
        None,
        description="Title or role at the firm if shown on the card. Return null if not found.",
    )
    profile_url: str | None = Field(
        None,
        description=(
            "Absolute URL to this partner's individual profile page on the firm's site. "
            "Return null if not found."
        ),
    )
    linkedin_url: str | None = Field(
        None,
        description="LinkedIn URL if linked from the card. Return null if not found.",
    )
    x_url: str | None = Field(
        None,
        description="X/Twitter URL if linked from the card. Return null if not found.",
    )


class TeamListingPage(BaseModel):
    partners: list[PartnerListing] = Field(
        description="Investment partners listed on this page."
    )


# ─── Team, stage 2 (individual partner detail page) ───


class PartnerDetail(BaseModel):
    name: str | None = Field(
        None, description="Partner's full name. Return null if not found."
    )
    role: str | None = Field(
        None, description="Title or role at the firm. Return null if not found."
    )
    bio: str | None = Field(
        None,
        description=(
            "Biographical text about the partner, 1-3 sentences. Return null if not found."
        ),
    )
    linkedin_url: str | None = Field(
        None,
        description=(
            "LinkedIn URL if linked from this profile page. Return null if not found."
        ),
    )
    x_url: str | None = Field(
        None, description="X/Twitter URL if linked. Return null if not found."
    )
    education: str | None = Field(
        None,
        description="Education background if mentioned. Return null if not found.",
    )
    prior_experience: str | None = Field(
        None,
        description="Prior roles or companies if mentioned. Return null if not found.",
    )


# ─── Portfolio, stage 1 (listing page) ───


class CompanyListing(BaseModel):
    name: str = Field(description="Portfolio company name.")
    detail_url: str | None = Field(
        None,
        description=(
            "Absolute URL to this company's profile page on the firm's site. "
            "Return null if not found."
        ),
    )
    company_website: str | None = Field(
        None,
        description=(
            "The company's own external website if linked from the card. "
            "Return null if not found."
        ),
    )
    sector: str | None = Field(
        None,
        description="Sector or category tag if shown. Return null if not found.",
    )


class PortfolioListingPage(BaseModel):
    companies: list[CompanyListing] = Field(
        description="Portfolio companies listed on this page."
    )


# ─── Portfolio, stage 2 (individual company detail page) ───


class FounderItem(BaseModel):
    name: str = Field(description="Founder's full name.")
    role: str | None = Field(
        None, description="Founder's role at the company. Return null if not found."
    )


class CompanyDetail(BaseModel):
    name: str | None = Field(None, description="Company name. Return null if not found.")
    company_website: str | None = Field(
        None,
        description="The company's own external website. Return null if not found.",
    )
    linkedin_url: str | None = Field(
        None, description="Company's LinkedIn URL if linked. Return null if not found."
    )
    sector: str | None = Field(
        None, description="Sector or category. Return null if not found."
    )
    description: str | None = Field(
        None, description="Company description, 1-3 sentences. Return null if not found."
    )
    founders: list[FounderItem] | None = Field(
        None,
        description=(
            "Company founders if listed on this page. Return null if not found. "
            "Do not invent founders."
        ),
    )


# ─── Blog / news (one-stage only) ───


class BlogPostListing(BaseModel):
    title: str = Field(description="Post title.")
    url: str = Field(description="Absolute URL to the post.")
    author: str | None = Field(
        None, description="Author name if shown. Return null if not found."
    )
    published_at: str | None = Field(
        None,
        description=(
            "Publish date as shown on the page (ISO 8601 if possible, raw string otherwise). "
            "Return null if not found."
        ),
    )


class BlogListingPage(BaseModel):
    posts: list[BlogPostListing] = Field(
        description="Blog or news posts listed on this page."
    )


# --------------------------------------------------------------------------- #
# Prompts — pass alongside each schema.
# --------------------------------------------------------------------------- #


TEAM_LISTING_PROMPT = (
    "Extract up to 10 investment partners from this VC firm's team page. For "
    "each, capture name, role/title, the absolute URL to their individual "
    "profile page on this site, and any LinkedIn or X/Twitter URLs visible on "
    "the card. Only include current investing partners. Exclude support staff, "
    "operating partners, alumni, and advisors unless they are listed as "
    "investing partners. Return null for any field not visible on the page."
)

PARTNER_DETAIL_PROMPT = (
    "Extract details about this investment partner from their profile page. "
    "Capture name, role/title, a 1-3 sentence bio, LinkedIn URL, X/Twitter URL, "
    "education, and prior experience. Return null for any field not present."
)

PORTFOLIO_LISTING_PROMPT = (
    "Extract up to 10 portfolio companies from this VC firm's portfolio page. "
    "For each, capture company name, the absolute URL to this company's profile "
    "page on THIS FIRM'S site (not the company's own site), the company's "
    "external website if linked, and the sector or category tag if shown. "
    "Return null for any field not visible."
)

COMPANY_DETAIL_PROMPT = (
    "Extract details about this portfolio company from its profile page on the "
    "VC firm's site. Capture name, the company's own external website, LinkedIn "
    "URL, sector, a 1-3 sentence description, and a list of founders with their "
    "names and roles if listed. If founders are not listed on this page, return "
    "null for the founders field. Do not invent founders."
)

BLOG_LISTING_PROMPT = (
    "Extract up to 10 of the most recent blog posts or news items on this "
    "page. For each, capture title, absolute URL to the post, author name if "
    "shown, and publish date if shown. Return null for any field not present."
)


_MAX_RECORDS = 10


# --------------------------------------------------------------------------- #
# Extractor
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class VcFirmExtractor:
    """Two-stage structured extraction over a firm's team/portfolio/blog URLs."""

    web: StructuredWebFetcher

    # ----- team ----- #

    def extract_team(self, team_url: str) -> list[dict[str, Any]]:
        listing = self.web.fetch_structured(team_url, TeamListingPage, TEAM_LISTING_PROMPT)
        partners_raw = listing.get("partners") or []
        listing_records: list[dict[str, Any]] = []
        for entry in partners_raw[:_MAX_RECORDS]:
            if not isinstance(entry, dict):
                continue
            record = dict(entry)
            record["profile_url"] = _absolutise(team_url, record.get("profile_url"))
            listing_records.append(record)

        detail_urls = _unique_non_null([r.get("profile_url") for r in listing_records])
        if not detail_urls:
            return listing_records

        details = self.web.fetch_structured_batch(
            detail_urls, PartnerDetail, PARTNER_DETAIL_PROMPT
        )
        by_url = dict(zip(detail_urls, details, strict=True))

        return [_merge_non_null(r, by_url.get(r.get("profile_url"))) for r in listing_records]

    # ----- portfolio ----- #

    def extract_portfolio(self, portfolio_url: str) -> list[dict[str, Any]]:
        listing = self.web.fetch_structured(
            portfolio_url, PortfolioListingPage, PORTFOLIO_LISTING_PROMPT
        )
        companies_raw = listing.get("companies") or []
        listing_records: list[dict[str, Any]] = []
        for entry in companies_raw[:_MAX_RECORDS]:
            if not isinstance(entry, dict):
                continue
            record = dict(entry)
            record["detail_url"] = _absolutise(portfolio_url, record.get("detail_url"))
            record["company_website"] = _absolutise(
                portfolio_url, record.get("company_website")
            )
            listing_records.append(record)

        detail_urls = _unique_non_null([r.get("detail_url") for r in listing_records])
        if not detail_urls:
            return listing_records

        details = self.web.fetch_structured_batch(
            detail_urls, CompanyDetail, COMPANY_DETAIL_PROMPT
        )
        by_url = dict(zip(detail_urls, details, strict=True))

        return [_merge_non_null(r, by_url.get(r.get("detail_url"))) for r in listing_records]

    # ----- blog ----- #

    def extract_blog(self, blog_url: str) -> list[dict[str, Any]]:
        listing = self.web.fetch_structured(blog_url, BlogListingPage, BLOG_LISTING_PROMPT)
        posts_raw = listing.get("posts") or []
        out: list[dict[str, Any]] = []
        for entry in posts_raw[:_MAX_RECORDS]:
            if not isinstance(entry, dict):
                continue
            record = dict(entry)
            record["url"] = _absolutise(blog_url, record.get("url"))
            out.append(record)
        return out


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _absolutise(base: str, candidate: Any) -> str | None:
    if not isinstance(candidate, str) or not candidate:
        return None
    return urljoin(base, candidate)


def _unique_non_null(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _merge_non_null(
    base: dict[str, Any], overlay: dict[str, Any] | None
) -> dict[str, Any]:
    if not overlay:
        return base
    merged = dict(base)
    for key, value in overlay.items():
        if value is None:
            continue
        merged[key] = value
    return merged
