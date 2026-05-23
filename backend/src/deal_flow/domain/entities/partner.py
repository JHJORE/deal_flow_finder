from dataclasses import dataclass, field


@dataclass(frozen=True)
class Partner:
    name: str
    profile_url: str
    role: str | None = None
    bio: str | None = None
    linkedin_url: str | None = None
    x_url: str | None = None
    education: tuple[str, ...] = field(default_factory=tuple)
    prior_experience: tuple[str, ...] = field(default_factory=tuple)
