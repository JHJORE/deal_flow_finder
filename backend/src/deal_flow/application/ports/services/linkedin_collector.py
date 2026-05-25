from abc import ABC, abstractmethod
from collections.abc import Sequence


class LinkedInCollector(ABC):
    """Read-only collector for LinkedIn post activity.

    A single call covers many profile URLs in one upstream actor run; the
    adapter is responsible for grouping the flat dataset response back into a
    dict keyed by the input URL. Both personal and company LinkedIn URLs are
    accepted — the underlying actor handles both shapes identically.
    """

    @abstractmethod
    def fetch_posts(
        self,
        profile_urls: Sequence[str],
        *,
        max_posts: int,
        include_reactions: bool = False,
        include_comments: bool = False,
        max_reactions: int = 5,
        max_comments: int = 5,
        posted_limit: str | None = None,
    ) -> dict[str, list[dict]]:
        """Return raw post dicts grouped by source profile URL.

        ``posted_limit`` accepts harvestapi's vocabulary: '24h', 'week',
        'month', '3months', '6months', 'year'. URLs that yielded no posts
        should still appear in the result as empty lists, so callers can tell
        "no posts" apart from "actor never saw this URL".
        """
