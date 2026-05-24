from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Tweet:
    id: str
    text: str
    author_handle: str | None = None
    created_at: datetime | None = None
    like_count: int | None = None
    retweet_count: int | None = None
    reply_count: int | None = None
    quote_count: int | None = None
    view_count: int | None = None
    is_reply: bool = False
    in_reply_to_username: str | None = None
    retweeted_tweet: Tweet | None = None
    quoted_tweet: Tweet | None = None

    @property
    def is_retweet(self) -> bool:
        return self.retweeted_tweet is not None

    @property
    def is_quote(self) -> bool:
        return self.quoted_tweet is not None
