"""LLM ports — used by Phase 4/5. Implementations land in the next workspace."""

from __future__ import annotations

from typing import Protocol

from pipeline.entities.models import DigestCard, Signal


class LLMTagger(Protocol):
    def tag(self, text: str, taxonomy: tuple[str, ...]) -> tuple[str, ...]:
        """Classify ``text`` against ``taxonomy``, returning the tags that apply.

        Adapters are expected to be idempotent and side-effect free; callers
        should cache results out-of-band when desired.
        """
        ...


class DigestNarrator(Protocol):
    def narrate(self, signal: Signal) -> DigestCard:
        """Wrap a :class:`Signal` with human-facing copy ready for the digest UI."""
        ...
