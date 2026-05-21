"""Tag content with a controlled taxonomy. Stub — implemented in the signal workspace."""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.application.ports.llm import LLMTagger


@dataclass(frozen=True, slots=True)
class TagContent:
    """Classify posts and essays into theme tags from a fixed taxonomy.

    Contract for the next workspace:
        Input: an iterable of ``(text, source_id)`` pairs and a taxonomy
        tuple loaded from ``config/themes.yaml``.
        Output: a mapping from ``source_id`` to the tuple of tags that apply.
        The tagger must be deterministic across runs given the same inputs
        (achieved via temperature=0 on the LLM adapter).
    """

    tagger: LLMTagger

    def execute(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError(
            "TagContent is implemented in the signal-detection workspace; "
            "see this docstring for the contract."
        )
