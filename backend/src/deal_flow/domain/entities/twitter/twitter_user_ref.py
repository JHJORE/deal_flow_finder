from dataclasses import dataclass


@dataclass(frozen=True)
class TwitterUserRef:
    handle: str
    user_id: str | None = None
    name: str | None = None
    description: str | None = None
    followers_count: int | None = None
