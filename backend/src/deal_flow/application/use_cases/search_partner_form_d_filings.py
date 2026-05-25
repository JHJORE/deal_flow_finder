import re
from dataclasses import dataclass
from datetime import date, timedelta

from deal_flow.application.ports.repositories.board_seat_log import BoardSeatLog
from deal_flow.application.ports.services.sec_filing_searcher import (
    SecFilingSearcher,
)
from deal_flow.domain.entities.form_d_filing import FormDFiling
from deal_flow.domain.entities.partner_form_d_signal import PartnerFormDSignal
from deal_flow.domain.value_objects.date_range import DateRange
from deal_flow.domain.value_objects.form_d_related_person import FormDRelatedPerson

_MAX_AGE_DAYS = 180  # 6 months — older filings are stale, not actionable dealflow


@dataclass(frozen=True)
class SearchPartnerFormDFilingsInput:
    partner_name: str
    date_range: DateRange


class SearchPartnerFormDFilings:
    """Find recent Form D filings naming a VC partner — board-seat signal.

    Two-pass: EDGAR full-text search (coarse) + primary_doc.xml parse on each
    hit (precise). A filing is kept only when the partner's name appears in
    ``<relatedPersonsList>`` *and* lists them as a Director — dropping
    spurious full-text matches and fund-vehicle officer listings.
    """

    def __init__(self, searcher: SecFilingSearcher, log: BoardSeatLog) -> None:
        self._searcher = searcher
        self._log = log

    def execute(self, input: SearchPartnerFormDFilingsInput) -> PartnerFormDSignal:
        recency_floor = input.date_range.end - timedelta(days=_MAX_AGE_DAYS)
        effective_start = max(input.date_range.start, recency_floor)
        effective_range = DateRange(start=effective_start, end=input.date_range.end)
        hits = self._searcher.search_form_d(
            query=f'"{input.partner_name}"',
            start=effective_range.start,
            end=effective_range.end,
        )
        filings: list[FormDFiling] = []
        for hit in hits:
            doc = self._searcher.fetch_primary_doc(
                hit["accession_number"], hit["issuer_cik"]
            )
            related = tuple(
                FormDRelatedPerson(
                    first_name=(p.get("first_name") or "").strip(),
                    last_name=(p.get("last_name") or "").strip(),
                    relationships=tuple(p.get("relationships") or ()),
                    relationship_clarification=p.get("relationship_clarification") or None,
                )
                for p in doc.get("related_persons") or hit.get("related_persons") or []
            )
            if not _names_match(related, input.partner_name):
                continue
            if not _partner_is_director(input.partner_name, related):
                continue
            filings.append(
                FormDFiling(
                    accession_number=hit["accession_number"],
                    issuer_name=hit["issuer_name"] or doc.get("issuer_name") or "",
                    issuer_cik=hit["issuer_cik"],
                    filed_at=date.fromisoformat(hit["filed_at"]),
                    url=hit["url"],
                    total_offering_amount=hit.get("total_offering_amount"),
                    total_amount_sold=hit.get("total_amount_sold"),
                    related_persons=related,
                    is_pooled_investment_fund=bool(doc.get("is_pooled_investment_fund")),
                    industry_group=doc.get("industry_group"),
                )
            )
        signal = PartnerFormDSignal(
            partner_name=input.partner_name,
            date_range=effective_range,
            filings=tuple(filings),
        )
        self._log.append(signal)
        return signal


def _names_match(persons: tuple[FormDRelatedPerson, ...], query_name: str) -> bool:
    target = re.sub(r"\s+", " ", query_name.strip().lower())
    if not target:
        return False
    return any(
        re.sub(r"\s+", " ", f"{p.first_name} {p.last_name}".strip().lower()) == target
        for p in persons
    )


def _partner_is_director(
    partner_name: str, persons: tuple[FormDRelatedPerson, ...]
) -> bool:
    last = partner_name.split()[-1].lower()
    for person in persons:
        if person.last_name.lower() != last:
            continue
        if any("director" in (r or "").lower() for r in person.relationships):
            return True
    return False
