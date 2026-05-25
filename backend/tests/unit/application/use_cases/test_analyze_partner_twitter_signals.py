from collections.abc import Sequence
from datetime import UTC, datetime

from deal_flow.application.use_cases.aggregate_item_themes import (
    AggregatedThemes,
    AggregateItemThemes,
    AggregateItemThemesInput,
)
from deal_flow.application.use_cases.analyze_partner_twitter_signals import (
    AnalyzePartnerTwitterSignals,
    AnalyzePartnerTwitterSignalsInput,
    PreviousFollowings,
)
from deal_flow.application.use_cases.thematize_items import (
    ChannelSpec,
    ThematizableItem,
    ThematizeItems,
)
from deal_flow.domain.entities.social.item_theme import ItemTheme
from deal_flow.domain.entities.twitter.tweet import Tweet
from deal_flow.domain.entities.twitter.twitter_profile import TwitterProfile
from deal_flow.domain.entities.twitter.twitter_snapshot import TwitterSnapshot
from deal_flow.domain.entities.twitter.twitter_user_ref import TwitterUserRef


class _FakeThematize(ThematizeItems):
    def __init__(self, output: tuple[ItemTheme, ...]) -> None:
        self.output = output
        self.received: list[Sequence[ThematizableItem]] = []

    def execute(
        self, items: Sequence[ThematizableItem], spec: ChannelSpec
    ) -> tuple[ItemTheme, ...]:
        self.received.append(list(items))
        return self.output


class _FakeAggregate(AggregateItemThemes):
    def __init__(self, output: AggregatedThemes) -> None:
        self.output = output
        self.received: list[AggregateItemThemesInput] = []

    def execute(
        self, input: AggregateItemThemesInput, spec: ChannelSpec
    ) -> AggregatedThemes:
        self.received.append(input)
        return self.output


def _snapshot(
    *,
    tweets: tuple[Tweet, ...] = (),
    followings: tuple[TwitterUserRef, ...] = (),
) -> TwitterSnapshot:
    return TwitterSnapshot(
        handle="partner",
        collected_at=datetime.now(UTC),
        profile=TwitterProfile(handle="partner"),
        tweets=tweets,
        followings=followings,
    )


def _empty_themes() -> AggregatedThemes:
    return AggregatedThemes(general_theme="", topics=())


def test_empty_baseline_surfaces_no_new_followings():
    snapshot = _snapshot(
        followings=(TwitterUserRef(handle="founder1", user_id="111"),)
    )
    out = AnalyzePartnerTwitterSignals(
        _FakeThematize(()), _FakeAggregate(_empty_themes())
    ).execute(
        AnalyzePartnerTwitterSignalsInput(
            snapshot=snapshot, previous=PreviousFollowings.empty()
        )
    )
    assert out.new_followings == ()


def test_diff_surfaces_only_user_ids_absent_from_previous():
    snapshot = _snapshot(
        followings=(
            TwitterUserRef(handle="founder1", user_id="111"),
            TwitterUserRef(handle="founder2", user_id="222"),
            TwitterUserRef(handle="founder3", user_id="333"),
        )
    )
    previous = PreviousFollowings(
        user_ids=frozenset({"111"}), handles=frozenset({"founder1"})
    )
    out = AnalyzePartnerTwitterSignals(
        _FakeThematize(()), _FakeAggregate(_empty_themes())
    ).execute(
        AnalyzePartnerTwitterSignalsInput(snapshot=snapshot, previous=previous)
    )
    assert tuple(r.user_id for r in out.new_followings) == ("222", "333")


def test_diff_falls_back_to_handle_when_user_id_missing():
    snapshot = _snapshot(
        followings=(
            TwitterUserRef(handle="founder1", user_id=None),
            TwitterUserRef(handle="founder2", user_id=None),
        )
    )
    previous = PreviousFollowings(
        user_ids=frozenset(), handles=frozenset({"founder1"})
    )
    out = AnalyzePartnerTwitterSignals(
        _FakeThematize(()), _FakeAggregate(_empty_themes())
    ).execute(
        AnalyzePartnerTwitterSignalsInput(snapshot=snapshot, previous=previous)
    )
    assert tuple(r.handle for r in out.new_followings) == ("founder2",)


def test_pure_retweets_dropped_before_thematize():
    own = Tweet(id="1", text="partner's own take")
    rt = Tweet(id="2", text="", retweeted_tweet=Tweet(id="99", text="original"))
    snapshot = _snapshot(tweets=(own, rt))
    thematize = _FakeThematize(())
    AnalyzePartnerTwitterSignals(
        thematize, _FakeAggregate(_empty_themes())
    ).execute(
        AnalyzePartnerTwitterSignalsInput(
            snapshot=snapshot, previous=PreviousFollowings.empty()
        )
    )
    (received,) = thematize.received
    assert [i.id for i in received] == ["1"]


def test_quote_tweets_inline_quoted_text():
    quoted = Tweet(id="99", text="Sequoia announces fund")
    qt = Tweet(id="1", text="this matters", quoted_tweet=quoted)
    snapshot = _snapshot(tweets=(qt,))
    thematize = _FakeThematize(())
    AnalyzePartnerTwitterSignals(
        thematize, _FakeAggregate(_empty_themes())
    ).execute(
        AnalyzePartnerTwitterSignalsInput(
            snapshot=snapshot, previous=PreviousFollowings.empty()
        )
    )
    (received,) = thematize.received
    assert received[0].text == "this matters [quoting: Sequoia announces fund]"


def test_carries_both_stages_outputs_into_analysis():
    snapshot = _snapshot(tweets=(Tweet(id="1", text="agents"),))
    stage1 = (ItemTheme(id="1", themes=("agents",), is_substantive=True),)
    aggregate = _FakeAggregate(
        AggregatedThemes(
            general_theme="Enterprise agent investor.", topics=("agents", "evals")
        )
    )
    out = AnalyzePartnerTwitterSignals(_FakeThematize(stage1), aggregate).execute(
        AnalyzePartnerTwitterSignalsInput(
            snapshot=snapshot, previous=PreviousFollowings.empty()
        )
    )
    assert out.general_theme == "Enterprise agent investor."
    assert out.topics == ("agents", "evals")
    assert out.item_themes == stage1
    (agg_input,) = aggregate.received
    assert agg_input.item_themes == stage1
    # Twitter orchestrator passes a "RECENTLY FOLLOWED ACCOUNTS" extra block.
    assert any(
        h == "RECENTLY FOLLOWED ACCOUNTS" for h, _ in agg_input.extra_context_blocks
    )


def test_previous_followings_from_following_refs_builds_both_sets():
    refs = (
        TwitterUserRef(handle="a", user_id="1"),
        TwitterUserRef(handle="b", user_id=None),
        TwitterUserRef(handle="", user_id="3"),
    )
    previous = PreviousFollowings.from_following_refs(refs)
    assert previous.user_ids == frozenset({"1", "3"})
    assert previous.handles == frozenset({"a", "b"})
