from dataclasses import dataclass, field

from deal_flow.domain.entities.twitter.twitter_snapshot import TwitterSnapshot


@dataclass(frozen=True)
class Partner:
    name: str
    profile_url: str
    role: str | None = None
    role_display: str | None = None
    focus_areas: tuple[str, ...] = field(default_factory=tuple)
    teams: tuple[str, ...] = field(default_factory=tuple)
    bio: str | None = None
    about_short: str | None = None
    linkedin_url: str | None = None
    x_url: str | None = None
    farcaster_url: str | None = None
    email: str | None = None
    photo_url: str | None = None
    # Sector / stage tags the firm publishes for this partner — e.g.
    # ("Seed/Early",), ("Growth", "Bio + Health"). Comes from the firm's
    # own labelling on the team page; empty when the firm doesn't tag.
    focus_areas: tuple[str, ...] = field(default_factory=tuple)
    education: tuple[str, ...] = field(default_factory=tuple)
    prior_experience: tuple[str, ...] = field(default_factory=tuple)
    twitter: TwitterSnapshot | None = None
