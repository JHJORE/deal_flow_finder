from __future__ import annotations

from pipeline.application.use_cases.query_edgar_filings import QueryEdgarFilings
from pipeline.entities.models import Filing, Partner, new_id
from pipeline.entities.value_objects import Cik, FirmName, Timestamp, Url
from pipeline.tests.application.fakes import FakeFilingFetcher


def _partner(name: str) -> Partner:
    return Partner(
        id=new_id(),
        name=name,
        firm=FirmName.SEQUOIA,
        role="Partner",
        x_handle=None,
        linkedin_url=None,
        blog_url=None,
        bio="",
    )


def _filing(accession: str, name: str = "Acme Co") -> Filing:
    return Filing(
        cik=Cik(1234567),
        issuer_name=name,
        raise_amount=1_000_000,
        filing_date=Timestamp.now(),
        form_type="D",
        accession_number=accession,
        source_url=Url("https://efts.sec.gov/x"),
    )


def test_drops_middle_initials_in_query() -> None:
    fetcher = FakeFilingFetcher(filings_by_name={("Mary", "Meeker"): [_filing("A1")]})
    out = QueryEdgarFilings(filings=fetcher).execute([_partner("Mary L. Meeker")])
    assert fetcher.calls == [("Mary", "Meeker")]
    assert [h.filing.accession_number for h in out] == ["A1"]
    assert out[0].partner.name == "Mary L. Meeker"


def test_skips_single_token_names() -> None:
    fetcher = FakeFilingFetcher()
    out = QueryEdgarFilings(filings=fetcher).execute([_partner("Madonna")])
    assert fetcher.calls == []
    assert out == []


def test_dedupes_across_partners_by_accession() -> None:
    fetcher = FakeFilingFetcher(
        filings_by_name={
            ("Roelof", "Botha"): [_filing("X1"), _filing("X2")],
            ("Mary", "Meeker"): [_filing("X2"), _filing("X3")],
        }
    )
    out = QueryEdgarFilings(filings=fetcher).execute(
        [_partner("Roelof Botha"), _partner("Mary L. Meeker")]
    )
    accessions = [h.filing.accession_number for h in out]
    assert sorted(accessions) == ["X1", "X2", "X3"]


def test_multi_word_last_name_uses_last_token() -> None:
    fetcher = FakeFilingFetcher(filings_by_name={("Roelof", "X"): [_filing("Y1")]})
    QueryEdgarFilings(filings=fetcher).execute([_partner("Roelof Botha van der X")])
    assert fetcher.calls == [("Roelof", "X")]
