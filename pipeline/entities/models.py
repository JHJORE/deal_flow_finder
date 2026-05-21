"""Domain entities.

Frozen dataclasses, validated in ``__post_init__``. Identifiers are
``uuid4().hex`` strings created via :func:`new_id`. Timestamps are always
:class:`Timestamp` value objects — never raw ``datetime``.

These entities are the contract that the signal-detection and frontend
workspaces depend on. Adding a field is backwards compatible; renaming or
removing one is not.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from pipeline.entities.errors import ValidationError
from pipeline.entities.value_objects import (
    Cik,
    EngagementType,
    FirmName,
    Handle,
    Sector,
    SignalKind,
    Stage,
    Timestamp,
    Url,
)


def new_id() -> str:
    """Generate a fresh uuid4 hex id. Centralised so tests can monkeypatch."""
    return uuid4().hex


# --------------------------------------------------------------------------- #
# Firm-graph entities
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Firm:
    name: FirmName
    website: Url
    people_page_url: Url
    portfolio_page_url: Url
    blog_url: Url | None
    edgar_aliases: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.edgar_aliases:
            raise ValidationError(f"Firm {self.name} must have at least one EDGAR alias")


@dataclass(frozen=True, slots=True)
class Partner:
    id: str
    name: str
    firm: FirmName
    role: str
    x_handle: Handle | None
    linkedin_url: Url | None
    blog_url: Url | None
    bio: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("Partner.name cannot be empty")


@dataclass(frozen=True, slots=True)
class Company:
    id: str
    name: str
    website: Url | None
    sector: Sector | None
    stage: Stage
    invested_by: tuple[FirmName, ...]
    founder_ids: tuple[str, ...]
    description: str
    linkedin_company_url: Url | None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("Company.name cannot be empty")


@dataclass(frozen=True, slots=True)
class WatchlistEntry:
    """A tracked operator whose LinkedIn we poll for stealth-transition signals.

    Lives in the entities layer because it is a first-class domain concept
    — what the fund considers a high-signal departure — independent of how
    the list is sourced (YAML today; a real CRM tomorrow).
    """

    name: str
    linkedin_url: Url
    prior_employer: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("WatchlistEntry.name cannot be empty")


@dataclass(frozen=True, slots=True)
class Founder:
    id: str
    name: str
    x_handle: Handle | None
    linkedin_url: Url | None
    company_id: str | None
    role: str
    prior_employer: str | None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("Founder.name cannot be empty")


# --------------------------------------------------------------------------- #
# Social entities
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Post:
    id: str
    author_handle: Handle
    text: str
    timestamp: Timestamp
    url: Url
    like_count: int
    reply_count: int
    repost_count: int

    def __post_init__(self) -> None:
        for name, value in (
            ("like_count", self.like_count),
            ("reply_count", self.reply_count),
            ("repost_count", self.repost_count),
        ):
            if value < 0:
                raise ValidationError(f"Post.{name} cannot be negative: {value}")


@dataclass(frozen=True, slots=True)
class Engagement:
    id: str
    actor_handle: Handle
    target_handle: Handle
    kind: EngagementType
    timestamp: Timestamp
    target_post_id: str | None
    context: str


@dataclass(frozen=True, slots=True)
class SocialSnapshot:
    handle: Handle
    captured_at: Timestamp
    follower_count: int
    following_count: int
    post_count_30d: int
    post_count_prior_30d: int

    def __post_init__(self) -> None:
        for name, value in (
            ("follower_count", self.follower_count),
            ("following_count", self.following_count),
            ("post_count_30d", self.post_count_30d),
            ("post_count_prior_30d", self.post_count_prior_30d),
        ):
            if value < 0:
                raise ValidationError(f"SocialSnapshot.{name} cannot be negative: {value}")


# --------------------------------------------------------------------------- #
# LinkedIn entities
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class LinkedInProfile:
    linkedin_url: Url
    captured_at: Timestamp
    current_title: str
    current_company: str
    headline: str
    recent_role_change: bool


@dataclass(frozen=True, slots=True)
class LinkedInCompany:
    linkedin_url: Url
    captured_at: Timestamp
    name: str
    headcount: int | None
    recent_senior_hires: tuple[dict[str, Any], ...]


# --------------------------------------------------------------------------- #
# Filings
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Filing:
    cik: Cik
    issuer_name: str
    raise_amount: int | None
    named_investors: tuple[str, ...]
    filing_date: Timestamp
    form_type: str
    accession_number: str
    source_url: Url

    def __post_init__(self) -> None:
        if not self.issuer_name.strip():
            raise ValidationError("Filing.issuer_name cannot be empty")
        if self.raise_amount is not None and self.raise_amount < 0:
            raise ValidationError(f"Filing.raise_amount cannot be negative: {self.raise_amount}")


# --------------------------------------------------------------------------- #
# Content
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class BlogPost:
    id: str
    author_partner_id: str
    title: str
    body: str
    published_at: Timestamp
    source_url: Url


# --------------------------------------------------------------------------- #
# Signals and digest
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Signal:
    id: str
    kind: SignalKind
    score: float
    evidence: dict[str, Any]
    detected_at: Timestamp
    narrative: str | None

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValidationError(f"Signal.score must be in [0, 1], got {self.score}")


@dataclass(frozen=True, slots=True)
class DigestCard:
    signal: Signal
    headline: str
    one_liner: str
    evidence_chips: tuple[str, ...]
    drill_down_url: Url


@dataclass(frozen=True, slots=True)
class Digest:
    generated_at: Timestamp
    cards: tuple[DigestCard, ...]
    meta: dict[str, Any] = field(default_factory=dict)
