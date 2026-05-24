from dataclasses import dataclass, field

from deal_flow.domain.entities.twitter.twitter_snapshot import TwitterSnapshot


@dataclass(frozen=True)
class Partner:
    name: str
    profile_url: str
    role: str | None = None
    bio: str | None = None
    linkedin_url: str | None = None
    x_url: str | None = None
    email: str | None = None
    photo_url: str | None = None
    education: tuple[str, ...] = field(default_factory=tuple)
    prior_experience: tuple[str, ...] = field(default_factory=tuple)
    twitter: TwitterSnapshot | None = None
