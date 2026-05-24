import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from urllib.parse import urlparse

from deal_flow.application.ports.services.twitter_collector import TwitterCollector
from deal_flow.domain.entities.partner import Partner
from deal_flow.domain.entities.twitter.tweet import Tweet
from deal_flow.domain.entities.twitter.twitter_profile import TwitterProfile
from deal_flow.domain.entities.twitter.twitter_snapshot import TwitterSnapshot
from deal_flow.domain.entities.twitter.twitter_user_ref import TwitterUserRef


@dataclass(frozen=True)
class EnrichPartnerWithTwitterInput:
    partner: Partner
    max_tweets: int = 100
    max_followings: int = 200
    max_mentions: int = 40


class EnrichPartnerWithTwitter:
    """Attach raw Twitter signals to a single Partner.

    If the partner has no parseable ``x_url``, it's returned unchanged. Otherwise
    we pull profile + last_tweets + followings + mentions from the collector,
    derive retweets and quote-tweets as subsets of the tweets feed (no extra
    calls), and replace the partner's ``twitter`` field.
    """

    def __init__(self, collector: TwitterCollector) -> None:
        self._collector = collector

    def execute(self, input: EnrichPartnerWithTwitterInput) -> Partner:
        handle = handle_from_x_url(input.partner.x_url)
        if handle is None:
            return input.partner

        profile_raw = self._collector.fetch_profile(handle)
        tweets_raw = self._collector.fetch_last_tweets(handle, input.max_tweets)
        followings_raw = self._collector.fetch_followings(handle, input.max_followings)
        mentions_raw = self._collector.fetch_mentions(handle, input.max_mentions)

        tweets = tuple(_to_tweet(t) for t in tweets_raw)
        mentions = tuple(_to_tweet(m) for m in mentions_raw)
        followings = tuple(_to_user_ref(f) for f in followings_raw)

        snapshot = TwitterSnapshot(
            handle=handle,
            collected_at=datetime.now(UTC),
            profile=_to_profile(profile_raw, handle),
            tweets=tweets,
            followings=followings,
            mentions=mentions,
            retweets=tuple(t for t in tweets if t.is_retweet),
            quote_tweets=tuple(t for t in tweets if t.is_quote),
        )
        return replace(input.partner, twitter=snapshot)


_HANDLE_RE = re.compile(r"^[A-Za-z0-9_]{1,15}$")
_TWITTER_HOSTS = {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}


def handle_from_x_url(x_url: str | None) -> str | None:
    """Pull the screen-name out of an x.com / twitter.com profile URL.

    Returns the lower-cased handle on success, ``None`` if we can't extract a
    plausible one. Exposed (not underscored) because the route also uses it to
    match a URL-supplied handle against partners.
    """
    if not x_url:
        return None
    parsed = urlparse(x_url.strip())
    host = (parsed.netloc or "").lower()
    if host not in _TWITTER_HOSTS:
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if not parts or not _HANDLE_RE.match(parts[0]):
        return None
    return parts[0].lower()


def _to_profile(raw: dict, handle: str) -> TwitterProfile:
    return TwitterProfile(
        handle=(raw.get("userName") or handle).lower(),
        user_id=_str_or_none(raw.get("id")),
        name=raw.get("name"),
        description=raw.get("description"),
        followers_count=_int_or_none(raw.get("followers")),
        following_count=_int_or_none(raw.get("following")),
        statuses_count=_int_or_none(raw.get("statusesCount")),
        created_at=_parse_dt(raw.get("createdAt")),
        verified=raw.get("isBlueVerified"),
        profile_url=raw.get("url"),
    )


def _to_tweet(raw: dict) -> Tweet:
    author = raw.get("author") or {}
    retweeted = raw.get("retweeted_tweet")
    quoted = raw.get("quoted_tweet")
    return Tweet(
        id=_str_or_none(raw.get("id")) or "",
        text=raw.get("text") or "",
        author_handle=_lower_or_none(author.get("userName")),
        created_at=_parse_dt(raw.get("createdAt")),
        like_count=_int_or_none(raw.get("likeCount")),
        retweet_count=_int_or_none(raw.get("retweetCount")),
        reply_count=_int_or_none(raw.get("replyCount")),
        quote_count=_int_or_none(raw.get("quoteCount")),
        view_count=_int_or_none(raw.get("viewCount")),
        is_reply=bool(raw.get("isReply")),
        in_reply_to_username=_lower_or_none(raw.get("inReplyToUsername")),
        retweeted_tweet=_to_tweet(retweeted) if isinstance(retweeted, dict) else None,
        quoted_tweet=_to_tweet(quoted) if isinstance(quoted, dict) else None,
    )


def _to_user_ref(raw: dict) -> TwitterUserRef:
    return TwitterUserRef(
        handle=(raw.get("userName") or "").lower(),
        user_id=_str_or_none(raw.get("id")),
        name=raw.get("name"),
        description=raw.get("description"),
        followers_count=_int_or_none(raw.get("followers")),
    )


def _str_or_none(value: object) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _int_or_none(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _lower_or_none(value: object) -> str | None:
    s = _str_or_none(value)
    return s.lower() if s else None


def _parse_dt(value: object) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    text = str(value)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        pass
    # Twitter classic format: "Wed Oct 10 20:19:24 +0000 2018"
    try:
        return datetime.strptime(text, "%a %b %d %H:%M:%S %z %Y")
    except ValueError:
        return None
