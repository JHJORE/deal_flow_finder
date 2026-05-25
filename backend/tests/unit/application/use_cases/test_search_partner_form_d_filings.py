from datetime import date, timedelta

from deal_flow.application.ports.repositories.board_seat_log import BoardSeatLog
from deal_flow.application.ports.services.sec_filing_searcher import (
    SecFilingSearcher,
)
from deal_flow.application.use_cases.search_partner_form_d_filings import (
    SearchPartnerFormDFilings,
    SearchPartnerFormDFilingsInput,
)
from deal_flow.domain.entities.partner_form_d_signal import PartnerFormDSignal
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


class _FakeLog(BoardSeatLog):
    def __init__(self) -> None:
        self.appended: list[PartnerFormDSignal] = []

    def append(self, signal: PartnerFormDSignal) -> None:
        self.appended.append(signal)


def _director_hit(**overrides) -> dict:
    base = {
        "accession_number": "0001483900-10-000004",
        "issuer_name": "Mixed Media Labs, Inc.",
        "issuer_cik": "0001483900",
        "filed_at": "2010-11-16",
        "url": "https://www.sec.gov/x",
        "total_offering_amount": 5_000_000,
        "total_amount_sold": 5_000_000,
    }
    base.update(overrides)
    return base


def test_use_case_quotes_partner_name_and_forwards_window():
    searcher = _FakeSearcher(hits=[])
    window = DateRange(start=date(2026, 2, 23), end=date(2026, 5, 24))

    signal = SearchPartnerFormDFilings(searcher, _FakeLog()).execute(
        SearchPartnerFormDFilingsInput(partner_name="Marc Andreessen", date_range=window)
    )

    assert searcher.calls == [('"Marc Andreessen"', window.start, window.end)]
    assert signal.partner_name == "Marc Andreessen"
    assert signal.date_range == window
    assert signal.filings == ()


def test_use_case_maps_director_hit_to_filing():
    adsh = "0001483900-10-000004"
    searcher = _FakeSearcher(
        hits=[_director_hit()],
        related_by_adsh={
            adsh: [
                {
                    "first_name": "Marc",
                    "last_name": "Andreessen",
                    "relationships": ["Director"],
                    "relationship_clarification": None,
                }
            ]
        },
    )

    signal = SearchPartnerFormDFilings(searcher, _FakeLog()).execute(
        SearchPartnerFormDFilingsInput(
            partner_name="Marc Andreessen",
            date_range=DateRange(start=date(2010, 1, 1), end=date(2010, 12, 31)),
        )
    )

    (filing,) = signal.filings
    assert filing.accession_number == adsh
    assert filing.issuer_name == "Mixed Media Labs, Inc."
    assert filing.issuer_cik == "0001483900"
    assert filing.filed_at == date(2010, 11, 16)
    assert filing.total_offering_amount == 5_000_000
    assert filing.total_amount_sold == 5_000_000
    (person,) = filing.related_persons
    assert person.first_name == "Marc"
    assert person.last_name == "Andreessen"
    assert person.relationships == ("Director",)


def test_use_case_drops_hits_without_partner_in_related_persons():
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
            "0001-MATCH": [
                {"first_name": "Marc", "last_name": "Andreessen", "relationships": ["Director"]}
            ],
            "0002-NOISE": [
                {"first_name": "Someone", "last_name": "Else", "relationships": ["Director"]}
            ],
        },
    )

    signal = SearchPartnerFormDFilings(searcher, _FakeLog()).execute(
        SearchPartnerFormDFilingsInput(
            partner_name="Marc Andreessen",
            date_range=DateRange(start=date(2026, 1, 1), end=date(2026, 5, 24)),
        )
    )

    assert [f.accession_number for f in signal.filings] == ["0001-MATCH"]


def test_use_case_drops_filings_where_partner_is_only_a_fund_officer():
    searcher = _FakeSearcher(
        hits=[
            {
                "accession_number": "0001829459-21-000001",
                "issuer_name": "Andreessen Horowitz LSV Fund II-B, L.P.",
                "issuer_cik": "0001829459",
                "filed_at": "2021-02-23",
                "url": "https://www.sec.gov/x",
            }
        ],
        related_by_adsh={
            "0001829459-21-000001": [
                {
                    "first_name": "Marc",
                    "last_name": "Andreessen",
                    "relationships": ["Executive Officer"],
                    "relationship_clarification": "Managing Member of the General Partner",
                }
            ]
        },
    )

    signal = SearchPartnerFormDFilings(searcher, _FakeLog()).execute(
        SearchPartnerFormDFilingsInput(
            partner_name="Marc Andreessen",
            date_range=DateRange(start=date(2020, 1, 1), end=date(2021, 12, 31)),
        )
    )

    assert signal.filings == ()


def test_use_case_appends_filtered_signal_to_log():
    adsh = "0001483900-10-000004"
    searcher = _FakeSearcher(
        hits=[
            _director_hit(),
            {
                "accession_number": "noop",
                "issuer_name": "Some Fund LP",
                "issuer_cik": "0000999999",
                "filed_at": "2010-11-16",
                "url": "https://www.sec.gov/x",
            },
        ],
        related_by_adsh={
            adsh: [
                {
                    "first_name": "Marc",
                    "last_name": "Andreessen",
                    "relationships": ["Director"],
                    "relationship_clarification": None,
                }
            ],
            "noop": [
                {
                    "first_name": "Marc",
                    "last_name": "Andreessen",
                    "relationships": ["Executive Officer"],
                    "relationship_clarification": None,
                }
            ],
        },
    )
    log = _FakeLog()

    SearchPartnerFormDFilings(searcher, log).execute(
        SearchPartnerFormDFilingsInput(
            partner_name="Marc Andreessen",
            date_range=DateRange(start=date(2010, 1, 1), end=date(2010, 12, 31)),
        )
    )

    (recorded,) = log.appended
    assert len(recorded.filings) == 1
    assert recorded.filings[0].accession_number == adsh


def test_use_case_caps_search_window_to_six_months():
    searcher = _FakeSearcher(hits=[])
    long_window = DateRange(start=date(2020, 1, 1), end=date(2026, 5, 24))

    signal = SearchPartnerFormDFilings(searcher, _FakeLog()).execute(
        SearchPartnerFormDFilingsInput(partner_name="X", date_range=long_window)
    )

    (_, start, end) = searcher.calls[0]
    assert end == date(2026, 5, 24)
    assert start == date(2026, 5, 24) - timedelta(days=180)
    assert signal.date_range.start == start


def test_use_case_keeps_filing_when_partner_is_director_even_if_others_are_officers():
    adsh = "0001483900-10-000004"
    searcher = _FakeSearcher(
        hits=[_director_hit()],
        related_by_adsh={
            adsh: [
                {
                    "first_name": "Some",
                    "last_name": "CEO",
                    "relationships": ["Executive Officer"],
                    "relationship_clarification": None,
                },
                {
                    "first_name": "Marc",
                    "last_name": "Andreessen",
                    "relationships": ["Director"],
                    "relationship_clarification": None,
                },
            ]
        },
    )

    signal = SearchPartnerFormDFilings(searcher, _FakeLog()).execute(
        SearchPartnerFormDFilingsInput(
            partner_name="Marc Andreessen",
            date_range=DateRange(start=date(2010, 1, 1), end=date(2010, 12, 31)),
        )
    )

    assert len(signal.filings) == 1
