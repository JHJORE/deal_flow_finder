from dataclasses import dataclass
from datetime import UTC, datetime

from deal_flow.application.use_cases.aggregate_item_themes import (
    AggregateItemThemes,
    AggregateItemThemesInput,
)
from deal_flow.application.use_cases.thematize_items import (
    ChannelSpec,
    ThematizableItem,
    ThematizeItems,
)
from deal_flow.domain.entities.twitter.tweet import Tweet
from deal_flow.domain.entities.twitter.twitter_analysis import TwitterAnalysis
from deal_flow.domain.entities.twitter.twitter_profile import TwitterProfile
from deal_flow.domain.entities.twitter.twitter_snapshot import TwitterSnapshot
from deal_flow.domain.entities.twitter.twitter_user_ref import TwitterUserRef

_TOP_K = 10

_SPEC = ChannelSpec(
    platform="Twitter/X",
    passthrough="retweet",
    stage1_schema_name="item_themes_twitter_v1",
    stage2_schema_name="aggregate_themes_twitter_v1",
)


@dataclass(frozen=True)
class PreviousFollowings:
    """Baseline followings from a previously persisted snapshot.

    Both id and handle sets are kept because ``user_id`` is the stable join
    key (handles change, IDs don't) but some older cached entries may only
    have handles.
    """

    user_ids: frozenset[str]
    handles: frozenset[str]

    @classmethod
    def empty(cls) -> "PreviousFollowings":
        return cls(user_ids=frozenset(), handles=frozenset())

    @classmethod
    def from_following_refs(
        cls, refs: tuple[TwitterUserRef, ...]
    ) -> "PreviousFollowings":
        return cls(
            user_ids=frozenset(r.user_id for r in refs if r.user_id),
            handles=frozenset(r.handle for r in refs if r.handle),
        )


@dataclass(frozen=True)
class AnalyzePartnerTwitterSignalsInput:
    snapshot: TwitterSnapshot
    previous: PreviousFollowings


class AnalyzePartnerTwitterSignals:
    """Twitter-side orchestrator: convert Tweets → ThematizableItems, run the
    shared two-stage analysis, diff followings against the previous snapshot."""

    def __init__(
        self, thematize: ThematizeItems, aggregate: AggregateItemThemes
    ) -> None:
        self._thematize = thematize
        self._aggregate = aggregate

    def execute(
        self, input: AnalyzePartnerTwitterSignalsInput
    ) -> TwitterAnalysis:
        snapshot = input.snapshot
        items = tuple(_to_item(t) for t in snapshot.tweets if t.id and not _is_pure_retweet(t))
        item_themes = self._thematize.execute(items, _SPEC)
        top_texts = tuple(
            (t.text or "").replace("\n", " ").strip()
            for t in _top_by_engagement(snapshot.tweets, _TOP_K)
        )
        aggregated = self._aggregate.execute(
            AggregateItemThemesInput(
                profile_block=_twitter_profile_block(snapshot.profile),
                item_themes=item_themes,
                top_engagement_texts=top_texts,
                extra_context_blocks=(
                    ("RECENTLY FOLLOWED ACCOUNTS", _format_followings(snapshot.followings)),
                ),
            ),
            _SPEC,
        )
        return TwitterAnalysis(
            general_theme=aggregated.general_theme,
            topics=aggregated.topics,
            item_themes=item_themes,
            new_followings=_diff_new(snapshot.followings, input.previous),
            analyzed_at=datetime.now(UTC),
        )


def _to_item(t: Tweet) -> ThematizableItem:
    text = (t.text or "").replace("\n", " ").replace("\t", " ").strip()
    if t.is_quote and t.quoted_tweet is not None:
        quoted = (t.quoted_tweet.text or "").replace("\n", " ").replace("\t", " ").strip()
        if quoted:
            text = f"{text} [quoting: {quoted}]"
    return ThematizableItem(id=t.id, text=text)


def _is_pure_retweet(t: Tweet) -> bool:
    return t.is_retweet and not t.is_quote and not (t.text or "").strip()


def _top_by_engagement(tweets: tuple[Tweet, ...], k: int) -> tuple[Tweet, ...]:
    def score(t: Tweet) -> int:
        return (
            (t.like_count or 0)
            + (t.retweet_count or 0)
            + (t.reply_count or 0)
            + (t.quote_count or 0)
        )

    return tuple(sorted(tweets, key=score, reverse=True)[:k])


def _diff_new(
    current: tuple[TwitterUserRef, ...], previous: PreviousFollowings
) -> tuple[TwitterUserRef, ...]:
    if not previous.user_ids and not previous.handles:
        return ()
    out: list[TwitterUserRef] = []
    for ref in current:
        if ref.user_id:
            if ref.user_id not in previous.user_ids:
                out.append(ref)
        elif ref.handle and ref.handle not in previous.handles:
            out.append(ref)
    return tuple(out)


def _twitter_profile_block(profile: TwitterProfile) -> str:
    parts = [f"handle: @{profile.handle}"]
    if profile.name:
        parts.append(f"name: {profile.name}")
    if profile.description:
        parts.append(f"bio: {profile.description}")
    return "\n".join(parts)


def _format_followings(refs: tuple[TwitterUserRef, ...]) -> str:
    lines: list[str] = []
    for r in refs:
        name = r.name or r.handle
        bio = (r.description or "").replace("\n", " ").strip()
        lines.append(f"- @{r.handle} ({name}): {bio}" if bio else f"- @{r.handle} ({name})")
    return "\n".join(lines) if lines else "(no recent followings)"
