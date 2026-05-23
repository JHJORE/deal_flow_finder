from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class BlogPost:
    title: str
    url: str
    author: str | None = None
    published_at: date | None = None
