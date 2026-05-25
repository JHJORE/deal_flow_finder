from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LinkedInComment:
    text: str
    author_name: str | None = None
    author_url: str | None = None
    author_headline: str | None = None
    posted_at: datetime | None = None
    like_count: int | None = None
