from datetime import date

from deal_flow.application.ports.services.sec_filing_searcher import (
    SecFilingSearcher,
)
from deal_flow.application.use_cases.search_partner_form_d_filings import (
    SearchPartnerFormDFilings,
    SearchPartnerFormDFilingsInput,
)
from deal_flow.domain.value_objects.date_range import DateRange


class _FakeSearcher(SecFilingSearcher):
    def __init__(self, hits: list[dict], related_by_adsh: dict[str, list[dict]] | None = None) -> None:
        self.hits = hits
        self.related_by_adsh = related_by_adsh or {}
        self.calls: list[tuple[str, date, date]] = []

    def search_form_d(self, query, start, end):
        self.calls.append((query, start, end))
        return self.hits

    def fetch_primary_doc(self, accession_number: str, cik: str) -> dict:
        return {
            "issuer_name": "",
            "related_persons": self.related_by_adsh.get(accession_number, []),
            "industry_group": None,
            "is_pooled_investment_fund": False,
        }


def test_use_case_quotes_partner_name_and_forwards_window():
    searcher = _FakeSearcher(hits=[])
    window = DateRange(start=date(2026, 2, 23), end=date(2026, 5, 24))

    signal = SearchPartnerFormDFilings(searcher).execute(
        SearchPartnerFormDFilingsInput(partner_name="Marc Andreessen", date_range=window)
    )

    assert searcher.calls == [('"Marc Andreessen"', window.start, window.end)]
    assert signal.partner_name == "Marc Andreessen"
    assert signal.date_range == window
    assert signal.filings == ()


def test_use_case_maps_hits_to_filings():
    searcher = _FakeSearcher(
        hits=[
            {
                "accession_number": "0001483900-10-000004",
                "issuer_name": "Mixed Media Labs, Inc.",
                "issuer_cik": "0001483900",
                "filed_at": "2010-11-16",
                "url": "https://www.sec.gov/Archives/edgar/data/1483900/000148390010000004/0001483900-10-000004-index.htm",
            }
        ],
        related_by_adsh={
            "0001483900-10-000004": [
                {"first_name": "Marc", "last_name": "Andreessen", "relationships": ["Director"]}
            ]
        },
    )

    signal = SearchPartnerFormDFilings(searcher).execute(
        SearchPartnerFormDFilingsInput(
            partner_name="Marc Andreessen",
            date_range=DateRange(start=date(2010, 1, 1), end=date(2010, 12, 31)),
        )
    )

    (filing,) = signal.filings
    assert filing.accession_number == "0001483900-10-000004"
    assert filing.issuer_name == "Mixed Media Labs, Inc."
    assert filing.issuer_cik == "0001483900"
    assert filing.filed_at == date(2010, 11, 16)


def test_use_case_drops_hits_without_partner_in_related_persons():
    """Full-text-search hits that don't actually name the partner in the
    structured relatedPersonsList are noise (the partner appears only in an
    address or signature block). The filter drops them."""
    searcher = _FakeSearcher(
        hits=[
            {
                "accession_number": "0001-MATCH",
                "issuer_name": "Real Hit",
                "issuer_cik": "1",
                "filed_at": "2026-01-01",
                "url": "x",
            },
            {
                "accession_number": "0002-NOISE",
                "issuer_name": "Spurious",
                "issuer_cik": "2",
                "filed_at": "2026-01-02",
                "url": "y",
            },
        ],
        related_by_adsh={
            "0001-MATCH": [{"first_name": "Marc", "last_name": "Andreessen", "relationships": ["Director"]}],
            "0002-NOISE": [{"first_name": "Someone", "last_name": "Else", "relationships": ["Director"]}],
        },
    )

    signal = SearchPartnerFormDFilings(searcher).execute(
        SearchPartnerFormDFilingsInput(
            partner_name="Marc Andreessen",
            date_range=DateRange(start=date(2026, 1, 1), end=date(2026, 5, 24)),
        )
    )

    assert [f.accession_number for f in signal.filings] == ["0001-MATCH"]
