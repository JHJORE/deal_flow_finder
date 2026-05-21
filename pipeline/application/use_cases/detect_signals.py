"""Detect signals from tagged content + activity snapshots. Stub."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DetectSignals:
    """Run every signal detector over the current collection snapshot.

    Contract for the next workspace:
        Input: the firm graph (``data/firm_graph.json``), reconciled filings
        (``data/filings.json``), social activity (``data/social/``),
        LinkedIn profile changes (``data/linkedin/``), and tagged content.
        Output: a list of :class:`pipeline.entities.models.Signal` written to
        ``data/signals.json``. One detector per :class:`SignalKind` value,
        each returning ``Optional[Signal]``. Scores are calibrated against
        the prior period's snapshot — never absolute counts.
    """

    def execute(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError(
            "DetectSignals is implemented in the signal-detection workspace; "
            "see this docstring for the contract."
        )
