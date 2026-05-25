from dataclasses import dataclass, field
from datetime import datetime

from deal_flow.domain.entities.linkedin.linkedin_analysis import LinkedInAnalysis
from deal_flow.domain.entities.linkedin.linkedin_post import LinkedInPost


@dataclass(frozen=True)
class LinkedInSnapshot:
    profile_url: str
    collected_at: datetime
    posts: tuple[LinkedInPost, ...] = field(default_factory=tuple)
    reposts: tuple[LinkedInPost, ...] = field(default_factory=tuple)
    quote_posts: tuple[LinkedInPost, ...] = field(default_factory=tuple)
    analysis: LinkedInAnalysis | None = None
