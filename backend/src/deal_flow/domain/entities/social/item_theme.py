from dataclasses import dataclass


@dataclass(frozen=True)
class ItemTheme:
    """Per-item LLM classification, shared across social channels.

    ``id`` joins back to the source item (``Tweet.id`` or ``LinkedInPost.id``)
    in the same snapshot. ``is_substantive`` is false for trivial replies so
    partner-level aggregation can skip them.
    """

    id: str
    themes: tuple[str, ...]
    is_substantive: bool
