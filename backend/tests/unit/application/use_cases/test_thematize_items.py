from typing import Any

from deal_flow.application.ports.services.llm_structured_output import (
    LlmStructuredOutput,
)
from deal_flow.application.use_cases.thematize_items import (
    ChannelSpec,
    ThematizableItem,
    ThematizeItems,
)

_TWITTER_SPEC = ChannelSpec(
    platform="Twitter/X",
    passthrough="retweet",
    stage1_schema_name="item_themes_twitter_v1",
    stage2_schema_name="aggregate_themes_twitter_v1",
)
_LINKEDIN_SPEC = ChannelSpec(
    platform="LinkedIn",
    passthrough="repost",
    stage1_schema_name="item_themes_linkedin_v1",
    stage2_schema_name="aggregate_themes_linkedin_v1",
)


class _FakeLlm(LlmStructuredOutput):
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.prompts: list[str] = []
        self.schema_names: list[str] = []

    def generate(self, *, prompt: str, response_schema, schema_name: str) -> dict:
        self.prompts.append(prompt)
        self.schema_names.append(schema_name)
        return self.response


def test_prompt_includes_every_item_id_and_text():
    llm = _FakeLlm({"item_themes": []})
    items = [
        ThematizableItem(id="1", text="agents are eating the enterprise"),
        ThematizableItem(id="2", text="voice AI is the new consumer interface"),
    ]
    ThematizeItems(llm).execute(items, _TWITTER_SPEC)
    (prompt,) = llm.prompts
    assert "1\tagents are eating the enterprise" in prompt
    assert "2\tvoice AI is the new consumer interface" in prompt
    assert llm.schema_names == ["item_themes_twitter_v1"]


def test_spec_platform_words_appear_in_prompt():
    llm = _FakeLlm({"item_themes": []})
    ThematizeItems(llm).execute([ThematizableItem(id="1", text="x")], _LINKEDIN_SPEC)
    prompt = llm.prompts[0]
    assert "LinkedIn posts" in prompt
    assert "repost" in prompt
    assert "Twitter/X" not in prompt


def test_returns_item_theme_per_id_in_response():
    llm = _FakeLlm(
        {
            "item_themes": [
                {"id": "1", "themes": ["AI agents", "enterprise"], "is_substantive": True},
                {"id": "2", "themes": ["voice AI"], "is_substantive": False},
            ]
        }
    )
    result = ThematizeItems(llm).execute(
        [ThematizableItem(id="1", text="x"), ThematizableItem(id="2", text="y")],
        _TWITTER_SPEC,
    )
    assert [t.id for t in result] == ["1", "2"]
    assert result[0].themes == ("AI agents", "enterprise")
    assert result[0].is_substantive is True
    assert result[1].is_substantive is False


def test_empty_input_skips_llm_call():
    llm = _FakeLlm({"item_themes": []})
    assert ThematizeItems(llm).execute([], _TWITTER_SPEC) == ()
    assert llm.prompts == []


def test_malformed_response_items_skipped():
    llm = _FakeLlm(
        {
            "item_themes": [
                {"id": "", "themes": ["x"], "is_substantive": True},  # blank id → drop
                {"id": "2", "themes": [None, "voice AI", ""], "is_substantive": True},
            ]
        }
    )
    result = ThematizeItems(llm).execute(
        [ThematizableItem(id="2", text="y")], _TWITTER_SPEC
    )
    assert [t.id for t in result] == ["2"]
    assert result[0].themes == ("voice AI",)
