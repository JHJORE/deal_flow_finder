from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TwitterProfile:
    handle: str
    user_id: str | None = None
    name: str | None = None
    description: str | None = None
    followers_count: int | None = None
    following_count: int | None = None
    statuses_count: int | None = None
    created_at: datetime | None = None
    verified: bool | None = None
    profile_url: str | None = None
