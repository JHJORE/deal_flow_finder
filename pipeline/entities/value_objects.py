"""Value objects.

Value objects make illegal states unrepresentable. A ``Handle`` is not a
``str``; a ``Url`` is not a ``str``; a ``Timestamp`` is always UTC-aware.
Anywhere in ``core`` or ``application`` that traffics in these primitives,
the type itself is the validation.

All value objects are frozen dataclasses that validate in ``__post_init__``.
Construction failures raise :class:`pipeline.entities.errors.ValidationError` —
never a stray ``ValueError`` — so callers have one error type to handle.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from pipeline.entities.errors import ValidationError


@dataclass(frozen=True, slots=True)
class Handle:
    """A social handle (X / Twitter). Stored without the leading ``@``."""

    value: str

    def __post_init__(self) -> None:
        raw = self.value.strip()
        if raw.startswith("@"):
            raw = raw[1:]
        if not raw:
            raise ValidationError("Handle cannot be empty")
        if any(ch.isspace() for ch in raw):
            raise ValidationError(f"Handle must not contain whitespace: {self.value!r}")
        # Frozen dataclass: bypass the setattr lock to normalise in place.
        object.__setattr__(self, "value", raw)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


@dataclass(frozen=True, slots=True)
class Url:
    """An absolute http(s) URL."""

    value: str

    def __post_init__(self) -> None:
        raw = self.value.strip()
        if not raw:
            raise ValidationError("Url cannot be empty")
        if not (raw.startswith("http://") or raw.startswith("https://")):
            raise ValidationError(f"Url must start with http:// or https://: {self.value!r}")
        object.__setattr__(self, "value", raw)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


@dataclass(frozen=True, slots=True)
class Timestamp:
    """A UTC-aware datetime. Naive datetimes are rejected at construction."""

    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo is None:
            raise ValidationError("Timestamp must be timezone-aware")
        # Normalise everything to UTC so downstream comparisons are total.
        object.__setattr__(self, "value", self.value.astimezone(UTC))

    @classmethod
    def now(cls) -> Timestamp:
        return cls(datetime.now(UTC))

    @classmethod
    def from_iso(cls, iso: str) -> Timestamp:
        try:
            parsed = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValidationError(f"Invalid ISO timestamp: {iso!r}") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return cls(parsed)

    def iso(self) -> str:
        return self.value.isoformat()


@dataclass(frozen=True, slots=True)
class Cik:
    """SEC Central Index Key. 1-10 digit integer."""

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool):
            raise ValidationError(f"Cik must be int, got {type(self.value).__name__}")
        if self.value <= 0 or self.value > 9_999_999_999:
            raise ValidationError(f"Cik out of range: {self.value}")

    def padded(self) -> str:
        """Zero-padded 10-digit form as used in EDGAR URLs."""
        return f"{self.value:010d}"


@dataclass(frozen=True, slots=True)
class Sector:
    """Free-form sector tag, normalised to lowercase ASCII with single spaces."""

    value: str

    def __post_init__(self) -> None:
        raw = " ".join(self.value.lower().split())
        if not raw:
            raise ValidationError("Sector cannot be empty")
        object.__setattr__(self, "value", raw)


class FirmName(str, Enum):
    SEQUOIA = "sequoia"
    A16Z = "a16z"
    YCOMBINATOR = "ycombinator"


class EngagementType(str, Enum):
    POST = "post"
    LIKE = "like"
    REPLY = "reply"
    QUOTE = "quote"
    FOLLOW = "follow"
    MENTION = "mention"


class Stage(str, Enum):
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    GROWTH = "growth"
    UNKNOWN = "unknown"


class SignalKind(str, Enum):
    """Every signal the system can emit. Grouped by tier in comments.

    The signal-detection workspace consumes this enum; do not add new kinds
    without a corresponding detector design.
    """

    # Tier 1 — deal signals
    PARTNER_ENGAGEMENT_WITH_UNKNOWN = "partner_engagement_with_unknown"
    UNDISCLOSED_FORM_D = "undisclosed_form_d"
    SCOUT_INVESTMENT = "scout_investment"
    PARTNER_GONE_QUIET = "partner_gone_quiet"
    PARTNER_FOUNDER_FIRST_MUTUAL = "partner_founder_first_mutual"

    # Tier 2 — founder heat
    FOUNDER_POST_ACCELERATION = "founder_post_acceleration"
    FOUNDER_FOLLOWER_SPIKE = "founder_follower_spike"
    FIRST_SENIOR_LINKEDIN_HIRE = "first_senior_linkedin_hire"

    # Tier 3 — stealth and departure
    OPERATOR_STEALTH_TRANSITION = "operator_stealth_transition"
    CO_DEPARTURE_CLUSTER = "co_departure_cluster"
    TOP_LAB_RESEARCHER_DEPARTURE = "top_lab_researcher_departure"

    # Tier 4 — thesis and zeitgeist
    THEME_DRIFT = "theme_drift"
    PARTNER_ESSAY = "partner_essay"
    CONTRARIAN_PARTNER_STANCE = "contrarian_partner_stance"
    CROSS_PARTNER_THESIS_ALIGNMENT = "cross_partner_thesis_alignment"
    ENGAGEMENT_REVEALED_INTEREST = "engagement_revealed_interest"

    # Tier 5 — discovery
    NEW_YC_BATCH_ADDITION = "new_yc_batch_addition"
    NEW_PORTFOLIO_ADDITION = "new_portfolio_addition"
    NEW_PARTNER_AT_FIRM = "new_partner_at_firm"
