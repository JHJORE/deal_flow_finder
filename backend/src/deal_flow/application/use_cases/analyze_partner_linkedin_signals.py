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
from deal_flow.domain.entities.linkedin.linkedin_analysis import LinkedInAnalysis
from deal_flow.domain.entities.linkedin.linkedin_post import LinkedInPost
from deal_flow.domain.entities.linkedin.linkedin_snapshot import LinkedInSnapshot

_TOP_K = 10

_SPEC = ChannelSpec(
    platform="LinkedIn",
    passthrough="repost",
    stage1_schema_name="item_themes_linkedin_v1",
    stage2_schema_name="aggregate_themes_linkedin_v1",
)


class AnalyzePartnerLinkedInSignals:
    """LinkedIn-side orchestrator: convert posts → ThematizableItems, run the
    shared two-stage analysis. No diff — LinkedIn has no who-the-partner-follows
    signal."""

    def __init__(
        self, thematize: ThematizeItems, aggregate: AggregateItemThemes
    ) -> None:
        self._thematize = thematize
        self._aggregate = aggregate

    def execute(self, snapshot: LinkedInSnapshot) -> LinkedInAnalysis:
        items = tuple(
            _to_item(p) for p in snapshot.posts if p.id and not _is_pure_repost(p)
        )
        item_themes = self._thematize.execute(items, _SPEC)
        top_texts = tuple(
            (p.text or "").replace("\n", " ").strip()
            for p in _top_by_engagement(snapshot.posts, _TOP_K)
        )
        aggregated = self._aggregate.execute(
            AggregateItemThemesInput(
                profile_block=snapshot.profile_url or "(unknown)",
                item_themes=item_themes,
                top_engagement_texts=top_texts,
            ),
            _SPEC,
        )
        return LinkedInAnalysis(
            general_theme=aggregated.general_theme,
            topics=aggregated.topics,
            item_themes=item_themes,
            analyzed_at=datetime.now(UTC),
        )


def _to_item(p: LinkedInPost) -> ThematizableItem:
    text = (p.text or "").replace("\n", " ").replace("\t", " ").strip()
    if p.is_quote and p.quoted_post is not None:
        quoted = (p.quoted_post.text or "").replace("\n", " ").replace("\t", " ").strip()
        if quoted:
            text = f"{text} [quoting: {quoted}]"
    return ThematizableItem(id=p.id, text=text)


def _is_pure_repost(p: LinkedInPost) -> bool:
    return p.is_repost and not p.is_quote and not (p.text or "").strip()


def _top_by_engagement(
    posts: tuple[LinkedInPost, ...], k: int
) -> tuple[LinkedInPost, ...]:
    def score(p: LinkedInPost) -> int:
        return (
            (p.reactions_count or 0)
            + (p.comments_count or 0)
            + (p.reposts_count or 0)
        )

    return tuple(sorted(posts, key=score, reverse=True)[:k])
