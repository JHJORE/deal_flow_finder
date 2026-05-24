from dataclasses import dataclass
from datetime import date

from deal_flow.application.ports.services.sec_filing_searcher import (
    SecFilingSearcher,
)
from deal_flow.domain.entities.form_d_filing import FormDFiling
from deal_flow.domain.entities.partner_form_d_signal import PartnerFormDSignal
from deal_flow.domain.value_objects.date_range import DateRange


@dataclass(frozen=True)
class SearchPartnerFormDFilingsInput:
    partner_name: str
    date_range: DateRange


class SearchPartnerFormDFilings:
    """Find recent Form D filings naming a VC partner — board-seat signal."""

    def __init__(self, searcher: SecFilingSearcher) -> None:
        self._searcher = searcher

    def execute(self, input: SearchPartnerFormDFilingsInput) -> PartnerFormDSignal:
        hits = self._searcher.search_form_d(
            query=f'"{input.partner_name}"',
            start=input.date_range.start,
            end=input.date_range.end,
        )
        return PartnerFormDSignal(
            partner_name=input.partner_name,
            date_range=input.date_range,
            filings=tuple(_to_filing(hit) for hit in hits),
        )


def _to_filing(hit: dict) -> FormDFiling:
    return FormDFiling(
        accession_number=hit["accession_number"],
        issuer_name=hit["issuer_name"],
        issuer_cik=hit["issuer_cik"],
        filed_at=date.fromisoformat(hit["filed_at"]),
        url=hit["url"],
    )
