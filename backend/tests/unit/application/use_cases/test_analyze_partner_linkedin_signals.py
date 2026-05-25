from collections.abc import Sequence
from datetime import UTC, datetime

from deal_flow.application.use_cases.aggregate_item_themes import (
    AggregatedThemes,
    AggregateItemThemes,
    AggregateItemThemesInput,
)
from deal_flow.application.use_cases.analyze_partner_linkedin_signals import (
    AnalyzePartnerLinkedInSignals,
)
from deal_flow.application.use_cases.thematize_items import (
    ChannelSpec,
    ThematizableItem,
    ThematizeItems,
)
from deal_flow.domain.entities.linkedin.linkedin_post import LinkedInPost
from deal_flow.domain.entities.linkedin.linkedin_snapshot import LinkedInSnapshot
from deal_flow.domain.entities.social.item_theme import ItemTheme


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


def _snapshot(*, posts: tuple[LinkedInPost, ...] = ()) -> LinkedInSnapshot:
    return LinkedInSnapshot(
        profile_url="https://linkedin.com/in/partner",
        collected_at=datetime.now(UTC),
        posts=posts,
    )


def test_carries_both_stages_outputs_into_analysis():
    snapshot = _snapshot(posts=(LinkedInPost(id="1", text="agents"),))
    stage1 = (ItemTheme(id="1", themes=("agents",), is_substantive=True),)
    aggregate = _FakeAggregate(
        AggregatedThemes(
            general_theme="Enterprise agent investor.", topics=("agents", "evals")
        )
    )
    out = AnalyzePartnerLinkedInSignals(_FakeThematize(stage1), aggregate).execute(
        snapshot
    )
    assert out.general_theme == "Enterprise agent investor."
    assert out.topics == ("agents", "evals")
    assert out.item_themes == stage1
    (agg_input,) = aggregate.received
    assert agg_input.item_themes == stage1
    # LinkedIn orchestrator does NOT pass any extra context blocks.
    assert agg_input.extra_context_blocks == ()


def test_pure_reposts_dropped_before_thematize():
    own = LinkedInPost(id="1", text="own take")
    repost = LinkedInPost(
        id="2", text="", reposted_post=LinkedInPost(id="99", text="original")
    )
    snapshot = _snapshot(posts=(own, repost))
    thematize = _FakeThematize(())
    AnalyzePartnerLinkedInSignals(
        thematize, _FakeAggregate(AggregatedThemes(general_theme="", topics=()))
    ).execute(snapshot)
    (received,) = thematize.received
    assert [i.id for i in received] == ["1"]


def test_top_engagement_picked_by_reactions_plus_comments_plus_reposts():
    quiet = LinkedInPost(
        id="quiet", text="boring", reactions_count=1, comments_count=0, reposts_count=0
    )
    loud = LinkedInPost(
        id="loud",
        text="popular take",
        reactions_count=500,
        comments_count=20,
        reposts_count=30,
    )
    mid = LinkedInPost(
        id="mid", text="moderate", reactions_count=50, comments_count=10
    )
    snapshot = _snapshot(posts=(quiet, loud, mid))
    aggregate = _FakeAggregate(AggregatedThemes(general_theme="", topics=()))
    AnalyzePartnerLinkedInSignals(_FakeThematize(()), aggregate).execute(snapshot)
    (agg_input,) = aggregate.received
    # loud > mid > quiet by score; top_engagement_texts contains their text
    assert agg_input.top_engagement_texts == ("popular take", "moderate", "boring")
