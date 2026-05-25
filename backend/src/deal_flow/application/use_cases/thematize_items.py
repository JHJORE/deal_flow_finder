from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from deal_flow.application.ports.services.llm_structured_output import (
    LlmStructuredOutput,
)
from deal_flow.domain.entities.social.item_theme import ItemTheme


@dataclass(frozen=True)
class ThematizableItem:
    """Pre-filtered text ready for theming.

    Callers strip passthrough items (pure retweets, pure reposts) and inline
    any quoted text into ``text`` before passing items in. Keeping this shape
    minimal makes the use case channel-agnostic.
    """

    id: str
    text: str


@dataclass(frozen=True)
class ChannelSpec:
    """Channel-specific words slotted into the shared prompts and schema
    cache keys. Two values per channel — keeps the use case generic without
    needing to rewrite the whole prompt per channel."""

    platform: str          # "Twitter/X" / "LinkedIn"
    passthrough: str       # "retweet" / "repost"
    stage1_schema_name: str
    stage2_schema_name: str


_STAGE1_PROMPT = (
    "You are reading the recent {platform} posts of a venture-capital partner. "
    "For each post, output 1-3 short free-form themes describing what the post is about. "
    "Themes should be specific and may be emerging niches — e.g. "
    "'AI chip infrastructure', 'open-source dev tools', 'agent evals', 'founder advice'. "
    "Do NOT force posts into a fixed taxonomy. Repeated themes across posts are good — "
    "they let the downstream step see a partner's recurring interests.\n\n"
    "Mark a post is_substantive=false when it is trivial (one-line congrats, 'great post!', "
    "pure logistics like 'see you there'); otherwise true. Non-substantive posts should "
    "still receive themes if any topic is identifiable, but the flag tells the next stage "
    "to weight them lower.\n\n"
    "Pure {passthrough}s (no added commentary) have already been excluded from the list "
    "below — you are only seeing the partner's own voice. Quote posts include the partner's "
    "comment plus the quoted text; treat both as signal.\n\n"
    "Posts (each line is one post, ``<id>\\t<text>``):\n{posts}"
)

_STAGE1_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "item_themes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "themes": {"type": "array", "items": {"type": "string"}},
                    "is_substantive": {"type": "boolean"},
                },
                "required": ["id", "themes", "is_substantive"],
            },
        }
    },
    "required": ["item_themes"],
}


class ThematizeItems:
    """Stage 1: classify each item into 1-3 free-form themes.

    One batched LLM call. The caller is responsible for filtering passthroughs
    and pre-formatting quoted text into ``text`` — this keeps the use case
    channel-agnostic.
    """

    def __init__(self, llm: LlmStructuredOutput) -> None:
        self._llm = llm

    def execute(
        self, items: Sequence[ThematizableItem], spec: ChannelSpec
    ) -> tuple[ItemTheme, ...]:
        if not items:
            return ()
        posts_block = "\n".join(f"{i.id}\t{i.text}" for i in items if i.id)
        if not posts_block:
            return ()
        result = self._llm.generate(
            prompt=_STAGE1_PROMPT.format(
                platform=spec.platform,
                passthrough=spec.passthrough,
                posts=posts_block,
            ),
            response_schema=_STAGE1_SCHEMA,
            schema_name=spec.stage1_schema_name,
        )
        out: list[ItemTheme] = []
        for entry in result.get("item_themes") or ():
            iid = (entry.get("id") or "").strip()
            if not iid:
                continue
            themes = tuple(
                s.strip()
                for s in (entry.get("themes") or ())
                if isinstance(s, str) and s.strip()
            )
            out.append(
                ItemTheme(
                    id=iid,
                    themes=themes,
                    is_substantive=bool(entry.get("is_substantive", True)),
                )
            )
        return tuple(out)
