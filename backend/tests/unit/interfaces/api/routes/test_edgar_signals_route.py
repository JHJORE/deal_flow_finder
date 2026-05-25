from fastapi.testclient import TestClient

from deal_flow.application.ports.repositories.board_seat_log import BoardSeatLog
from deal_flow.application.ports.services.sec_filing_searcher import (
    SecFilingSearcher,
)
from deal_flow.domain.entities.partner import Partner
from deal_flow.infrastructure.persistence.output_store import OutputStore
from deal_flow.interfaces.api.app import app
from deal_flow.interfaces.api.dependencies import (
    get_board_seat_log,
    get_extract_firm_partners,
    get_output_store,
    get_sec_filing_searcher,
)


class _NoopStore(OutputStore):
    def __init__(self) -> None:  # bypass mkdir
        pass

    def write(self, payload, *parts):  # type: ignore[override]
        return None


class _NullLog(BoardSeatLog):
    def append(self, signal) -> None:
        pass


class _FakePartners:
    def execute(self, _input):
        return [Partner(name="Reid Hoffman", profile_url="")]


class _FakeSearcher(SecFilingSearcher):
    def search_form_d(self, query, start, end):
        return [
            {
                "accession_number": "0002033975-26-000001",
                "issuer_name": "Superhuman Platform Inc.",
                "issuer_cik": "0002033975",
                "filed_at": "2026-04-06",
                "url": "https://www.sec.gov/Archives/edgar/data/2033975/000203397526000001/0002033975-26-000001-index.htm",
            }
        ]

    def fetch_primary_doc(self, accession_number: str, cik: str) -> dict:
        return {
            "issuer_name": "Superhuman Platform Inc.",
            "related_persons": [
                {"first_name": "Reid", "last_name": "Hoffman", "relationships": ["Director"]}
            ],
            "industry_group": None,
            "is_pooled_investment_fund": False,
        }


def test_edgar_signals_route_returns_filings_for_each_partner():
    app.dependency_overrides[get_extract_firm_partners] = lambda: _FakePartners()
    app.dependency_overrides[get_sec_filing_searcher] = lambda: _FakeSearcher()
    app.dependency_overrides[get_output_store] = lambda: _NoopStore()
    app.dependency_overrides[get_board_seat_log] = lambda: _NullLog()
    try:
        with TestClient(app) as client:
            response = client.get(
                "/firms/a16z.com/edgar-signals", params={"days": 60, "limit": 1}
            )
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        signal = body[0]
        assert signal["partner_name"] == "Reid Hoffman"
        assert signal["date_range"]["start"] and signal["date_range"]["end"]
        assert len(signal["filings"]) == 1
        assert signal["filings"][0]["issuer_name"] == "Superhuman Platform Inc."
    finally:
        app.dependency_overrides.clear()


def test_edgar_signals_route_returns_404_for_unknown_firm():
    app.dependency_overrides[get_extract_firm_partners] = lambda: _FakePartners()
    app.dependency_overrides[get_sec_filing_searcher] = lambda: _FakeSearcher()
    app.dependency_overrides[get_output_store] = lambda: _NoopStore()
    app.dependency_overrides[get_board_seat_log] = lambda: _NullLog()
    try:
        with TestClient(app) as client:
            response = client.get("/firms/unknown.example/edgar-signals")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
