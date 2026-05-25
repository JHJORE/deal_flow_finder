from dataclasses import dataclass


@dataclass(frozen=True)
class LinkedInReaction:
    reaction_type: str | None = None
    actor_name: str | None = None
    actor_url: str | None = None
    actor_headline: str | None = None
