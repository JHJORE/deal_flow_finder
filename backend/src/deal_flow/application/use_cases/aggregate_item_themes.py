from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from deal_flow.application.ports.services.llm_structured_output import (
    LlmStructuredOutput,
)
from deal_flow.application.use_cases.thematize_items import ChannelSpec
from deal_flow.domain.entities.social.item_theme import ItemTheme

_STAGE2_PROMPT = (
    "You are summarising a venture-capital partner's recent {platform} activity into a "
    "partner-level thematic profile. You have:\n\n"
    "  1. The partner's profile context.\n"
    "  2. The list of themes already extracted from each of their recent substantive posts.\n"
    "  3. A handful of their highest-engagement post texts (for tone/voice colour).\n"
    "{extra_context_intro}\n"
    "Produce:\n"
    "  * ``general_theme``: 1-2 sentences describing what this partner posts about and "
    "what their public investing focus appears to be. Plain text. No marketing language. "
    "No 'is a partner at X' restatement.\n"
    "  * ``topics``: 3-8 short partner-level topic tags, clustering the per-post themes. "
    "Specific is good — 'AI chip infrastructure' beats 'AI'. Keep free-form: do not force "
    "into a fixed taxonomy.\n\n"
    "--- PROFILE ---\n{profile_block}\n\n"
    "--- PER-POST THEMES (substantive posts only) ---\n{themes_block}\n\n"
    "--- TOP-ENGAGEMENT POSTS ---\n{top_posts_block}{extra_context_blocks}"
)

_STAGE2_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "general_theme": {"type": "string"},
        "topics": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["general_theme", "topics"],
}


@dataclass(frozen=True)
class AggregateItemThemesInput:
    profile_block: str
    item_themes: tuple[ItemTheme, ...]
    top_engagement_texts: tuple[str, ...]
    # Optional channel-specific context (header, body) blocks appended to the
    # prompt — e.g. Twitter passes recent-followings bios here.
    extra_context_blocks: tuple[tuple[str, str], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AggregatedThemes:
    general_theme: str
    topics: tuple[str, ...]


class AggregateItemThemes:
    """Stage 2: reduce per-item themes + a few high-engagement post texts
    into a partner-level summary."""

    def __init__(self, llm: LlmStructuredOutput) -> None:
        self._llm = llm

    def execute(
        self, input: AggregateItemThemesInput, spec: ChannelSpec
    ) -> AggregatedThemes:
        extras = _format_extras(input.extra_context_blocks)
        result = self._llm.generate(
            prompt=_STAGE2_PROMPT.format(
                platform=spec.platform,
                profile_block=input.profile_block or "(unknown)",
                themes_block=_format_themes(input.item_themes),
                top_posts_block=_format_top(input.top_engagement_texts),
                extra_context_intro=(
                    "  4. Additional context provided below.\n\n" if extras else "\n"
                ),
                extra_context_blocks=extras,
            ),
            response_schema=_STAGE2_SCHEMA,
            schema_name=spec.stage2_schema_name,
        )
        general_theme = (result.get("general_theme") or "").strip()
        topics = tuple(
            s.strip()
            for s in (result.get("topics") or ())
            if isinstance(s, str) and s.strip()
        )
        return AggregatedThemes(general_theme=general_theme, topics=topics)


def _format_themes(themes: Sequence[ItemTheme]) -> str:
    lines = [
        f"- {', '.join(t.themes)}"
        for t in themes
        if t.is_substantive and t.themes
    ]
    return "\n".join(lines) if lines else "(no substantive posts thematised)"


def _format_top(texts: Sequence[str]) -> str:
    lines = [f"- {t}" for t in texts if t.strip()]
    return "\n".join(lines) if lines else "(no high-engagement posts)"


def _format_extras(blocks: Sequence[tuple[str, str]]) -> str:
    out: list[str] = []
    for header, body in blocks:
        out.append(f"\n\n--- {header} ---\n{body or '(none)'}")
    return "".join(out)
