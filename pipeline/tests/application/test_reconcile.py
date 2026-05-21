from __future__ import annotations

import logging

from pipeline.application.use_cases.query_edgar_filings import PartnerFilingHit
from pipeline.application.use_cases.reconcile_portfolio_with_filings import (
    ReconcilePortfolioWithFilings,
)
from pipeline.entities.models import Company, Filing, Founder, Partner, new_id
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


def _founder(name: str) -> Founder:
    return Founder(
        id=new_id(),
        name=name,
        x_handle=None,
        linkedin_url=None,
        company_id=None,
        role="Founder",
        prior_employer=None,
    )


def _partner(name: str = "Roelof Botha") -> Partner:
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


def _filing(
    name: str,
    accession: str,
    *,
    executive_officers: tuple[str, ...] = (),
) -> Filing:
    return Filing(
        cik=Cik(123),
        issuer_name=name,
        raise_amount=None,
        filing_date=Timestamp.now(),
        form_type="D",
        accession_number=accession,
        source_url=Url("https://efts.sec.gov/x"),
        executive_officers=executive_officers,
    )


def _hit(filing: Filing, partner: Partner | None = None) -> PartnerFilingHit:
    return PartnerFilingHit(filing=filing, partner=partner or _partner())


def test_splits_disclosed_and_undisclosed_by_issuer_name() -> None:
    companies = [_company("Stripe"), _company("Klarna")]
    hits = [_hit(_filing("Stripe", "F1")), _hit(_filing("Unknown Newco", "F2"))]
    result = ReconcilePortfolioWithFilings().execute(hits, companies)
    assert [h.filing.accession_number for h in result.disclosed] == ["F1"]
    assert [h.filing.accession_number for h in result.undisclosed] == ["F2"]


def test_founder_name_second_pass_reclassifies_as_disclosed() -> None:
    # Shell name doesn't match a portfolio company, but the Executive
    # Officer matches a known founder → disclosed.
    companies = [_company("Neon AI")]
    founders = [_founder("Jane Founder")]
    hits = [
        _hit(
            _filing(
                "Project Crimson LLC",
                "F1",
                executive_officers=("Jane Founder",),
            )
        )
    ]
    result = ReconcilePortfolioWithFilings().execute(hits, companies, founders)
    assert len(result.disclosed) == 1
    assert len(result.undisclosed) == 0


def test_case_and_whitespace_insensitive() -> None:
    companies = [_company("  STRIPE  ")]
    hits = [_hit(_filing("stripe", "F1"))]
    result = ReconcilePortfolioWithFilings().execute(hits, companies)
    assert len(result.disclosed) == 1


def test_stealth_deal_log_format(caplog: logging.LogRecord) -> None:
    companies: list[Company] = []
    hits = [
        _hit(
            _filing(
                "Project Crimson LLC",
                "F1",
                executive_officers=("Jane Founder",),
            ),
            partner=_partner("Mary L. Meeker"),
        )
    ]
    with caplog.at_level(  # type: ignore[attr-defined]
        logging.INFO,
        logger="pipeline.application.use_cases.reconcile_portfolio_with_filings",
    ):
        ReconcilePortfolioWithFilings().execute(hits, companies)
    joined = "\n".join(r.message for r in caplog.records)  # type: ignore[attr-defined]
    assert "[STEALTH DEAL FOUND]" in joined
    assert "Project Crimson LLC" in joined
    assert "Jane Founder" in joined
    assert "Mary L. Meeker" in joined
