from typing import Any

from deal_flow.application.ports.services.llm_structured_output import (
    LlmStructuredOutput,
)
from deal_flow.application.use_cases.aggregate_item_themes import (
    AggregateItemThemes,
    AggregateItemThemesInput,
)
from deal_flow.application.use_cases.thematize_items import ChannelSpec
from deal_flow.domain.entities.social.item_theme import ItemTheme

_SPEC = ChannelSpec(
    platform="Twitter/X",
    passthrough="retweet",
    stage1_schema_name="item_themes_twitter_v1",
    stage2_schema_name="aggregate_themes_twitter_v1",
)


class _FakeLlm(LlmStructuredOutput):
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.prompt: str = ""
        self.schema_name: str = ""

    def generate(self, *, prompt: str, response_schema, schema_name: str) -> dict:
        self.prompt = prompt
        self.schema_name = schema_name
        return self.response


def test_prompt_uses_per_item_themes_not_raw_text():
    llm = _FakeLlm({"general_theme": "x", "topics": ["agents"]})
    AggregateItemThemes(llm).execute(
        AggregateItemThemesInput(
            profile_block="handle: @patgrady\nbio: Partner at Sequoia",
            item_themes=(
                ItemTheme(id="1", themes=("agent reliability",), is_substantive=True),
                ItemTheme(
                    id="2",
                    themes=("evals", "agent reliability"),
                    is_substantive=True,
                ),
            ),
            top_engagement_texts=("reliability is the new benchmark",),
        ),
        _SPEC,
    )
    assert "agent reliability" in llm.prompt
    assert "evals, agent reliability" in llm.prompt
    assert "reliability is the new benchmark" in llm.prompt
    assert "Partner at Sequoia" in llm.prompt
    assert llm.schema_name == "aggregate_themes_twitter_v1"


def test_non_substantive_themes_excluded_from_prompt():
    llm = _FakeLlm({"general_theme": "x", "topics": []})
    AggregateItemThemes(llm).execute(
        AggregateItemThemesInput(
            profile_block="x",
            item_themes=(
                ItemTheme(id="1", themes=("logistics",), is_substantive=False),
                ItemTheme(id="2", themes=("agents",), is_substantive=True),
            ),
            top_engagement_texts=(),
        ),
        _SPEC,
    )
    assert "- agents" in llm.prompt
    assert "- logistics" not in llm.prompt


def test_extra_context_blocks_appended_with_headers():
    llm = _FakeLlm({"general_theme": "x", "topics": []})
    AggregateItemThemes(llm).execute(
        AggregateItemThemesInput(
            profile_block="x",
            item_themes=(),
            top_engagement_texts=(),
            extra_context_blocks=(
                ("RECENTLY FOLLOWED ACCOUNTS", "- @founder1 (Some Founder)"),
            ),
        ),
        _SPEC,
    )
    assert "--- RECENTLY FOLLOWED ACCOUNTS ---" in llm.prompt
    assert "@founder1" in llm.prompt


def test_returns_parsed_general_theme_and_topics():
    llm = _FakeLlm(
        {
            "general_theme": "  Focuses on enterprise AI reliability.  ",
            "topics": [" agent reliability ", "", "agent evals", None, "enterprise AI"],
        }
    )
    result = AggregateItemThemes(llm).execute(
        AggregateItemThemesInput(
            profile_block="x",
            item_themes=(),
            top_engagement_texts=(),
        ),
        _SPEC,
    )
    assert result.general_theme == "Focuses on enterprise AI reliability."
    assert result.topics == ("agent reliability", "agent evals", "enterprise AI")
