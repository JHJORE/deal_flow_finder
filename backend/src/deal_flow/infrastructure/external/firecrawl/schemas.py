"""Pydantic shapes + prompts we hand to Firecrawl's JSON-mode extraction.

These never leave the infrastructure layer; the application sees only the
plain dicts that come back. Iterate on field descriptions and prompts here
when extraction quality is wrong.

Rules:
- Flat shapes. Lists wrapped in a top-level object — never a bare root list.
- Every optional field has Optional[...] + Field(description=...) that ends
  with "Return null if not found." so the model doesn't hallucinate.
- Socials get explicit guidance — they're the high-value, easy-to-miss bits.
- Never use max_items / maxItems / minItems (causes hallucinated entries).
"""


from pydantic import BaseModel, Field

_LINKEDIN_HINT = (
    "Look for a LinkedIn profile link anywhere on the page — header, bio, "
    "footer, social icons. Return the full https://linkedin.com/... URL. "
    "Return null if not found."
)
_X_HINT = (
    "Look for an X (formerly Twitter) profile link anywhere on the page — "
    "header, bio, footer, social icons (the icon may be labeled X or Twitter). "
    "Return the full https://x.com/... or https://twitter.com/... URL. "
    "Return null if not found."
)


# ---------- partners ----------

class _PartnerListing(BaseModel):
    name: str = Field(description="Full name of the investment partner.")
    role: str | None = Field(
        default=None,
        description=(
            "Job title on the listing card (e.g. 'General Partner'). "
            "Return null if not found."
        ),
    )
    profile_url: str | None = Field(
        default=None,
        description=(
            "URL to the partner's individual profile page on this site. May be "
            "a relative path. Return null if the card isn't a link."
        ),
    )
    linkedin_url: str | None = Field(default=None, description=_LINKEDIN_HINT)
    x_url: str | None = Field(default=None, description=_X_HINT)


class PartnerListingPage(BaseModel):
    partners: list[_PartnerListing] = Field(
        description=(
            "Every investment partner shown on the team page (general partner, "
            "partner, investment partner). EXCLUDE operating staff, recruiters, "
            "marketing, comms, EAs. Return at most 10."
        )
    )


class PartnerDetail(BaseModel):
    role: str | None = Field(
        default=None,
        description="Job title on this profile page. Return null if not found.",
    )
    bio: str | None = Field(
        default=None,
        description=(
            "Full biography text as written on this profile page (multiple "
            "paragraphs if present). Return null if no bio is present."
        ),
    )
    linkedin_url: str | None = Field(default=None, description=_LINKEDIN_HINT)
    x_url: str | None = Field(default=None, description=_X_HINT)
    education: list[str] = Field(
        default_factory=list,
        description=(
            "Schools / degrees mentioned in the bio or a dedicated education "
            "section. One entry per institution or degree, verbatim. Empty list "
            "if nothing is mentioned."
        ),
    )
    prior_experience: list[str] = Field(
        default_factory=list,
        description=(
            "Prior companies / roles from the bio or a dedicated experience "
            "section. One entry per company/role, verbatim. Empty list if "
            "nothing is mentioned."
        ),
    )


PARTNER_LISTING_PROMPT = (
    "Extract every investment partner on this team page. Include each "
    "partner's profile URL (may be relative) and any LinkedIn/X links "
    "visible on the card or in a social-icon strip. Return at most 10."
)

PARTNER_DETAIL_PROMPT = (
    "This is a single investment partner's profile page. Extract their job "
    "title, full bio text, LinkedIn URL, X/Twitter URL, list of schools/"
    "degrees, and list of prior companies. Socials are usually social icons "
    "near the name — look carefully. Do not invent missing fields."
)


# ---------- portfolio ----------

class _PortfolioListing(BaseModel):
    name: str = Field(description="Company name on the portfolio listing card.")
    detail_url: str | None = Field(
        default=None,
        description=(
            "URL to the company's detail page on this site. May be relative. "
            "Return null if the card has no detail link."
        ),
    )
    website: str | None = Field(
        default=None,
        description="External company website if shown on the card. Return null if not shown.",
    )
    sector: str | None = Field(
        default=None,
        description="Sector/category tag on the card (e.g. 'AI'). Return null if not shown.",
    )


class PortfolioListingPage(BaseModel):
    companies: list[_PortfolioListing] = Field(
        description="Every portfolio company on the listing page. Return at most 10."
    )


class _FounderItem(BaseModel):
    name: str = Field(description="Founder's full name.")
    role: str | None = Field(
        default=None, description="Founder's role/title. Return null if not shown."
    )


class PortfolioDetail(BaseModel):
    website: str | None = Field(
        default=None,
        description=(
            "Company's external website URL, usually a 'Visit website' button. "
            "Return null if not found."
        ),
    )
    linkedin_url: str | None = Field(default=None, description=_LINKEDIN_HINT)
    sector: str | None = Field(
        default=None,
        description="Sector/category on the detail page. Return null if not shown.",
    )
    description: str | None = Field(
        default=None,
        description=(
            "Company description / what the company does, as written on the "
            "page. Return null if no description is present."
        ),
    )
    founders: list[_FounderItem] = Field(
        default_factory=list,
        description=(
            "Founders listed on the detail page, with name and role each. "
            "Empty list if no founders are listed — do not invent."
        ),
    )


PORTFOLIO_LISTING_PROMPT = (
    "Extract every portfolio company on this page with name, detail URL "
    "(may be relative), external website if shown, and sector tag if shown. "
    "Return at most 10."
)

PORTFOLIO_DETAIL_PROMPT = (
    "This is a portfolio company detail page. Extract external website, "
    "LinkedIn URL, sector, description, and founders (name + role). "
    "Founders may legitimately be absent."
)


# ---------- blog ----------

class _BlogPostItem(BaseModel):
    title: str = Field(description="Post title/headline.")
    url: str = Field(description="Absolute or relative URL of the full article.")
    author: str | None = Field(
        default=None,
        description="Author byline on the listing card. Return null if not shown.",
    )
    published_at: str | None = Field(
        default=None,
        description=(
            "Publication date in ISO 8601 (YYYY-MM-DD). Convert human-readable "
            "dates like 'May 12, 2024' to 2024-05-12. Return null if no date."
        ),
    )


class BlogPostPage(BaseModel):
    posts: list[_BlogPostItem] = Field(
        description="Every blog/news post on the listing. Return at most 10, most-recent first."
    )


BLOG_POSTS_PROMPT = (
    "Extract every blog/news post on this listing with title, article URL "
    "(may be relative), author byline if shown, and date in YYYY-MM-DD. "
    "Return at most 10, preferring most recent."
)
