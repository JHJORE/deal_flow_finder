from dataclasses import dataclass
from datetime import datetime

from deal_flow.domain.entities.social.item_theme import ItemTheme


@dataclass(frozen=True)
class LinkedInAnalysis:
    """LLM-derived reading of a partner's recent LinkedIn activity.

    Same two-stage shape as TwitterAnalysis, without the newly-following diff —
    LinkedIn's collector has no analogous longitudinal who-the-partner-follows
    signal.
    """

    general_theme: str
    topics: tuple[str, ...]
    item_themes: tuple[ItemTheme, ...]
    analyzed_at: datetime
