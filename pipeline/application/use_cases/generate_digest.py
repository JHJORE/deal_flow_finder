"""Compose the daily digest from the highest-scoring signals. Stub."""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.application.ports.llm import DigestNarrator


@dataclass(frozen=True, slots=True)
class GenerateDigest:
    """Pick the top 3-5 signals and wrap them in human copy.

    Contract for the next workspace:
        Input: ``Signal`` list from ``DetectSignals``, plus the firm graph
        for entity-name lookup. Output: a :class:`Digest` written to
        ``data/digest.json`` with one ``DigestCard`` per surfaced signal.
        Ordering is by score desc, ties broken by signal tier (Tier 1 wins).
    """

    narrator: DigestNarrator

    def execute(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError(
            "GenerateDigest is implemented in the signal-detection workspace; "
            "see this docstring for the contract."
        )
