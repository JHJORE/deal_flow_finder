from __future__ import annotations

from pipeline.application.use_cases.reconcile_portfolio_with_filings import (
    ReconcilePortfolioWithFilings,
)
from pipeline.entities.models import Company, Filing, new_id
from pipeline.entities.value_objects import Cik, FirmName, Stage, Timestamp, Url


def _company(name: str) -> Company:
    return Company(
        id=new_id(),
        name=name,
        website=Url("https://example.com"),
        sector=None,
        stage=Stage.UNKNOWN,
        invested_by=(FirmName.SEQUOIA,),
        founder_ids=(),
        description="",
        linkedin_company_url=None,
    )


def _filing(name: str, accession: str) -> Filing:
    return Filing(
        cik=Cik(123),
        issuer_name=name,
        raise_amount=None,
        named_investors=("Sequoia Capital",),
        filing_date=Timestamp.now(),
        form_type="D",
        accession_number=accession,
        source_url=Url("https://efts.sec.gov/x"),
    )


def test_splits_disclosed_and_undisclosed() -> None:
    companies = [_company("Stripe"), _company("Klarna")]
    filings = [_filing("Stripe", "F1"), _filing("Unknown Newco", "F2")]
    result = ReconcilePortfolioWithFilings().execute(filings, companies)
    assert [f.accession_number for f in result.disclosed] == ["F1"]
    assert [f.accession_number for f in result.undisclosed] == ["F2"]


def test_case_and_whitespace_insensitive() -> None:
    companies = [_company("  STRIPE  ")]
    filings = [_filing("stripe", "F1")]
    result = ReconcilePortfolioWithFilings().execute(filings, companies)
    assert len(result.disclosed) == 1
