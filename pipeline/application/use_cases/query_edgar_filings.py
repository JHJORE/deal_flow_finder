"""Pull Form D filings for one or more firm aliases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from pipeline.application.ports.filings import FilingFetcher
from pipeline.entities.errors import DomainError
from pipeline.entities.models import Filing
from pipeline.entities.value_objects import Timestamp


@dataclass(frozen=True, slots=True)
class QueryEdgarFilings:
    """Fetch Form D filings naming each alias as an investor.

    Returns the union across aliases, deduplicated by accession number.
    A partial failure on one alias does not abort the others.
    """

    filings: FilingFetcher

    def execute(self, aliases: list[str], lookback_days: int = 90) -> list[Filing]:
        since = Timestamp(Timestamp.now().value - timedelta(days=lookback_days))
        seen: set[str] = set()
        out: list[Filing] = []
        for alias in aliases:
            try:
                results = self.filings.search_form_d(alias, since)
            except DomainError:
                continue
            for filing in results:
                if filing.accession_number in seen:
                    continue
                seen.add(filing.accession_number)
                out.append(filing)
        return out
