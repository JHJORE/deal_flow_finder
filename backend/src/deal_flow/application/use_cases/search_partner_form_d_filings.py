import re
from dataclasses import dataclass
from datetime import date

from deal_flow.application.ports.services.sec_filing_searcher import (
    SecFilingSearcher,
)
from deal_flow.domain.entities.form_d_filing import FormDFiling
from deal_flow.domain.entities.partner_form_d_signal import PartnerFormDSignal
from deal_flow.domain.value_objects.date_range import DateRange
from deal_flow.domain.value_objects.form_d_related_person import FormDRelatedPerson


@dataclass(frozen=True)
class SearchPartnerFormDFilingsInput:
    partner_name: str
    date_range: DateRange


class SearchPartnerFormDFilings:
    """Find recent Form D filings naming a VC partner — board-seat signal.

    Two-pass: EDGAR full-text search (coarse) + primary_doc.xml parse on each
    hit (precise). A filing is kept only when the partner's name appears in
    ``<relatedPersonsList>``, dropping spurious full-text matches where the
    partner shows up in addresses or signature blocks.
    """

    def __init__(self, searcher: SecFilingSearcher) -> None:
        self._searcher = searcher

    def execute(self, input: SearchPartnerFormDFilingsInput) -> PartnerFormDSignal:
        hits = self._searcher.search_form_d(
            query=f'"{input.partner_name}"',
            start=input.date_range.start,
            end=input.date_range.end,
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
                for p in doc.get("related_persons") or []
            )
            if not _names_match(related, input.partner_name):
                continue
            filings.append(FormDFiling(
                accession_number=hit["accession_number"],
                issuer_name=hit["issuer_name"] or doc.get("issuer_name") or "",
                issuer_cik=hit["issuer_cik"],
                filed_at=date.fromisoformat(hit["filed_at"]),
                url=hit["url"],
                related_persons=related,
                is_pooled_investment_fund=bool(doc.get("is_pooled_investment_fund")),
                industry_group=doc.get("industry_group"),
            ))
        return PartnerFormDSignal(
            partner_name=input.partner_name,
            date_range=input.date_range,
            filings=tuple(filings),
        )


def _names_match(persons: tuple[FormDRelatedPerson, ...], query_name: str) -> bool:
    target = re.sub(r"\s+", " ", query_name.strip().lower())
    if not target:
        return False
    return any(
        re.sub(r"\s+", " ", f"{p.first_name} {p.last_name}".strip().lower()) == target
        for p in persons
    )
