"""Pull Form D filings for one or more scraped GP partners.

Each ``Partner`` from Phase 1 is tokenized into first / last name and
fed to the EDGAR adapter as a ``"first" AND "last" AND "Director"``
query. Returns a list of ``PartnerFilingHit`` so the downstream
reconciliation can attribute every stealth-deal flag to the partner
that surfaced it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from pipeline.application.ports.filings import FilingFetcher
from pipeline.entities.errors import DomainError
from pipeline.entities.models import Filing, Partner
from pipeline.entities.value_objects import Timestamp

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PartnerFilingHit:
    """A Form D filing surfaced by a specific scraped partner."""

    filing: Filing
    partner: Partner


@dataclass(frozen=True, slots=True)
class QueryEdgarFilings:
    """Fetch Form D filings naming each partner as a Director.

    Returns the union across partners, deduplicated by accession number.
    A partial failure on one partner does not abort the others.
    """

    filings: FilingFetcher

    def execute(
        self, partners: list[Partner], lookback_days: int = 180
    ) -> list[PartnerFilingHit]:
        since = Timestamp(Timestamp.now().value - timedelta(days=lookback_days))
        seen: set[str] = set()
        out: list[PartnerFilingHit] = []
        for partner in partners:
            tokens = partner.name.split()
            if len(tokens) < 2:
                logger.info(
                    "Skipping partner with single-token name: %r", partner.name
                )
                continue
            # Drop middle initials/names so the quoted-token EDGAR query
            # still matches filings that spell out or omit the middle name.
            first_name, last_name = tokens[0], tokens[-1]
            try:
                results = self.filings.search_form_d(first_name, last_name, since)
            except DomainError:
                logger.warning(
                    "EDGAR search failed for %s %s", first_name, last_name
                )
                continue
            for filing in results:
                if filing.accession_number in seen:
                    continue
                seen.add(filing.accession_number)
                out.append(PartnerFilingHit(filing=filing, partner=partner))
        return out
