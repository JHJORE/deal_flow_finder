"""Mark which Form D filings correspond to already-disclosed portfolio companies.

The undisclosed filings — those naming a tracked firm as investor but
without a matching portfolio entry — are the leading-edge data point. They
become the input to the Tier 1 ``UNDISCLOSED_FORM_D`` signal in the next
workspace.
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.entities.models import Company, Filing


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    disclosed: tuple[Filing, ...]
    undisclosed: tuple[Filing, ...]

    @property
    def filings(self) -> tuple[Filing, ...]:
        return self.disclosed + self.undisclosed


@dataclass(frozen=True, slots=True)
class ReconcilePortfolioWithFilings:
    def execute(self, filings: list[Filing], companies: list[Company]) -> ReconciliationResult:
        known_names = {_normalise(c.name) for c in companies}
        disclosed: list[Filing] = []
        undisclosed: list[Filing] = []
        for filing in filings:
            (disclosed if _normalise(filing.issuer_name) in known_names else undisclosed).append(
                filing
            )
        return ReconciliationResult(
            disclosed=tuple(disclosed),
            undisclosed=tuple(undisclosed),
        )


def _normalise(name: str) -> str:
    return " ".join(name.lower().split()).rstrip(",.")
