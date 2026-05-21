from __future__ import annotations

from pipeline.application.use_cases.query_edgar_filings import QueryEdgarFilings
from pipeline.entities.models import Filing
from pipeline.entities.value_objects import Cik, Timestamp, Url
from pipeline.tests.application.fakes import FakeFilingFetcher


def _filing(accession: str, name: str = "Acme Co") -> Filing:
    return Filing(
        cik=Cik(1234567),
        issuer_name=name,
        raise_amount=1_000_000,
        named_investors=("Sequoia Capital",),
        filing_date=Timestamp.now(),
        form_type="D",
        accession_number=accession,
        source_url=Url("https://efts.sec.gov/x"),
    )


def test_aggregates_across_aliases_and_dedupes() -> None:
    fetcher = FakeFilingFetcher(
        filings_by_alias={
            "Sequoia Capital": [_filing("A1"), _filing("A2")],
            "Sequoia Capital Operations": [_filing("A2"), _filing("A3")],
        }
    )
    out = QueryEdgarFilings(filings=fetcher).execute(
        ["Sequoia Capital", "Sequoia Capital Operations"]
    )
    assert {f.accession_number for f in out} == {"A1", "A2", "A3"}
