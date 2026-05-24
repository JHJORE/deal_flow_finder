from abc import ABC, abstractmethod


class TwitterCollector(ABC):
    """Read-only collector for one Twitter handle's raw signals.

    Methods are purpose-shaped (not generic primitives) and return plain dicts —
    the same convention as :class:`WebExtractor`. The use case maps the raw
    payloads to domain entities; pagination and capping happen inside the
    adapter so the application layer stays cursor-unaware.

    Implementations must be read-only: GET endpoints only, no write actions of
    any kind, no login flows.
    """

    @abstractmethod
    def fetch_profile(self, handle: str) -> dict:
        """Single user-info payload for the given screen name."""

    @abstractmethod
    def fetch_last_tweets(self, handle: str, max_count: int) -> list[dict]:
        """The user's recent tweets, paginated up to ``max_count``.

        Each item is a raw tweet dict whose discriminator fields
        (``isReply``, ``retweeted_tweet``, ``quoted_tweet``) let the use case
        partition originals / replies / retweets / quote-tweets without extra
        calls.
        """

    @abstractmethod
    def fetch_followings(self, handle: str, max_count: int) -> list[dict]:
        """Who this user follows, newest-first by follow date, capped at
        ``max_count``. Page 1 is the most-recent follows."""

    @abstractmethod
    def fetch_mentions(self, handle: str, max_count: int) -> list[dict]:
        """Tweets mentioning this user, paginated up to ``max_count``."""
