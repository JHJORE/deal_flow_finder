from dataclasses import dataclass
from datetime import datetime

from deal_flow.domain.entities.social.item_theme import ItemTheme
from deal_flow.domain.entities.twitter.twitter_user_ref import TwitterUserRef


@dataclass(frozen=True)
class TwitterAnalysis:
    """LLM-derived reading of a partner's recent Twitter activity.

    ``item_themes`` is Stage 1 — every substantive tweet tagged. ``general_theme``
    + ``topics`` is Stage 2 — partner-level summary. ``new_followings`` lists
    accounts the partner has started following since the previous snapshot,
    keyed by stable ``user_id`` (handles change, IDs don't).
    """

    general_theme: str
    topics: tuple[str, ...]
    item_themes: tuple[ItemTheme, ...]
    new_followings: tuple[TwitterUserRef, ...]
    analyzed_at: datetime
