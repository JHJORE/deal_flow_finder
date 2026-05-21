"""Mark which Form D filings correspond to already-disclosed portfolio companies.

Two-pass entity resolution:

1. Issuer-name match — normalised ``Filing.issuer_name`` against the
   normalised portfolio company names.
2. Founder-name match — if step 1 missed, check whether any name in
   ``Filing.executive_officers`` (extracted from Form D Item 3 Related
   Persons with relationship Executive Officer or Promoter) matches a
   known portfolio founder. This catches stealth C-Corps whose legal
   shell name ("Project Crimson LLC") doesn't match their public brand
   ("Neon AI") in the portfolio cache.

Anything still unmatched is a true stealth-deal candidate — logged with
the partner who surfaced it, the date of first sale, and the founder
name(s) for downstream LinkedIn resolution.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from pipeline.application.use_cases.query_edgar_filings import PartnerFilingHit
from pipeline.entities.models import Company, Founder

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    disclosed: tuple[PartnerFilingHit, ...]
    undisclosed: tuple[PartnerFilingHit, ...]

    @property
    def hits(self) -> tuple[PartnerFilingHit, ...]:
        return self.disclosed + self.undisclosed


@dataclass(frozen=True, slots=True)
class ReconcilePortfolioWithFilings:
    def execute(
        self,
        hits: list[PartnerFilingHit],
        companies: list[Company],
        founders: list[Founder] | None = None,
    ) -> ReconciliationResult:
        known_company_names = {_normalise(c.name) for c in companies}
        known_founder_names = {
            _normalise(f.name) for f in (founders or []) if f.name.strip()
        }

        disclosed: list[PartnerFilingHit] = []
        undisclosed: list[PartnerFilingHit] = []
        for hit in hits:
            filing = hit.filing
            if _normalise(filing.issuer_name) in known_company_names:
                disclosed.append(hit)
                continue
            officer_match = any(
                _normalise(name) in known_founder_names
                for name in filing.executive_officers
            )
            if officer_match:
                disclosed.append(hit)
                continue
            undisclosed.append(hit)
            _log_stealth_deal(hit)

        return ReconciliationResult(
            disclosed=tuple(disclosed),
            undisclosed=tuple(undisclosed),
        )


def _log_stealth_deal(hit: PartnerFilingHit) -> None:
    filing = hit.filing
    if filing.date_of_first_sale is not None:
        date_str = filing.date_of_first_sale.iso()
    else:
        # Prefix with ~ to mark the fallback (submission date, not the
        # true wire date) so reviewers can tell at a glance.
        date_str = f"~{filing.filing_date.iso()}"
    founder_str = ", ".join(filing.executive_officers) or "unknown"
    logger.info(
        "[STEALTH DEAL FOUND] Date of First Sale: %s | Entity: %s | Founder: %s | Partner: %s",
        date_str,
        filing.issuer_name,
        founder_str,
        hit.partner.name,
    )


def _normalise(name: str) -> str:
    return " ".join(name.lower().split()).rstrip(",.")
