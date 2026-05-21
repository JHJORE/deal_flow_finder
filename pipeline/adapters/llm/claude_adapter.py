"""Claude adapter — stubbed. Wired in the signal-detection workspace."""

from __future__ import annotations


class ClaudeAdapter:
    """Implements ``LLMTagger`` and ``DigestNarrator`` against Anthropic Claude.

    Contract for the next workspace:
        - ``tag(text, taxonomy)``: single-shot call with a system prompt
          asking the model to return JSON ``{"tags": [...]}``. Use
          temperature=0 for determinism.
        - ``narrate(signal)``: takes a ``Signal``, returns a ``DigestCard``
          whose ``headline``, ``one_liner``, and ``evidence_chips`` are
          model-generated. Keep prompts in a dedicated ``prompts/`` package
          rather than inline string literals.
    """

    def tag(self, text: str, taxonomy: tuple[str, ...]) -> tuple[str, ...]:
        raise NotImplementedError("ClaudeAdapter.tag is implemented in the signal workspace")

    def narrate(self, signal: object) -> object:
        raise NotImplementedError("ClaudeAdapter.narrate is implemented in the signal workspace")
