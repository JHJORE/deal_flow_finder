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
    def __init__(self, hits: list[dict]) -> None:
        self.hits = hits
        self.calls: list[tuple[str, date, date]] = []

    def search_form_d(self, query, start, end):
        self.calls.append((query, start, end))
        return self.hits


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
        ]
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
