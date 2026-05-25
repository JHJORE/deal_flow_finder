from dataclasses import dataclass, field
from datetime import datetime

from deal_flow.domain.entities.twitter.tweet import Tweet
from deal_flow.domain.entities.twitter.twitter_analysis import TwitterAnalysis
from deal_flow.domain.entities.twitter.twitter_profile import TwitterProfile
from deal_flow.domain.entities.twitter.twitter_user_ref import TwitterUserRef


@dataclass(frozen=True)
class TwitterSnapshot:
    handle: str
    collected_at: datetime
    profile: TwitterProfile
    tweets: tuple[Tweet, ...] = field(default_factory=tuple)
    followings: tuple[TwitterUserRef, ...] = field(default_factory=tuple)
    mentions: tuple[Tweet, ...] = field(default_factory=tuple)
    retweets: tuple[Tweet, ...] = field(default_factory=tuple)
    quote_tweets: tuple[Tweet, ...] = field(default_factory=tuple)
    analysis: TwitterAnalysis | None = None
