from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import respx

from pipeline.adapters.filings.edgar_adapter import SEARCH_ENDPOINT, EdgarFilingFetcher
from pipeline.entities.value_objects import Timestamp


def _fetcher() -> EdgarFilingFetcher:
    return EdgarFilingFetcher(httpx.Client())


_PRIMARY_DOC = """<?xml version="1.0"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/formd">
  <offeringData>
    <offeringSalesAmounts>
      <totalOfferingAmount>5000000</totalOfferingAmount>
    </offeringSalesAmounts>
    <dateOfFirstSale>
      <value>2025-01-10</value>
    </dateOfFirstSale>
  </offeringData>
  <relatedPersonsList>
    <relatedPersonInfo>
      <relatedPersonName>
        <relatedPersonFirstName>Roelof</relatedPersonFirstName>
        <relatedPersonLastName>Botha</relatedPersonLastName>
      </relatedPersonName>
      <relatedPersonRelationshipList>
        <relationship>Director</relationship>
      </relatedPersonRelationshipList>
    </relatedPersonInfo>
    <relatedPersonInfo>
      <relatedPersonName>
        <relatedPersonFirstName>Jane</relatedPersonFirstName>
        <relatedPersonLastName>Founder</relatedPersonLastName>
      </relatedPersonName>
      <relatedPersonRelationshipList>
        <relationship>Executive Officer</relationship>
      </relatedPersonRelationshipList>
    </relatedPersonInfo>
  </relatedPersonsList>
</edgarSubmission>
"""

_PRIMARY_DOC_YET_TO_OCCUR = """<?xml version="1.0"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/formd">
  <offeringData>
    <dateOfFirstSale>
      <yetToOccur/>
    </dateOfFirstSale>
  </offeringData>
  <relatedPersonsList>
    <relatedPersonInfo>
      <relatedPersonName>
        <relatedPersonFirstName>Pat</relatedPersonFirstName>
        <relatedPersonLastName>Promoter</relatedPersonLastName>
      </relatedPersonName>
      <relatedPersonRelationshipList>
        <relationship>Promoter</relationship>
      </relatedPersonRelationshipList>
    </relatedPersonInfo>
  </relatedPersonsList>
</edgarSubmission>
"""


def _recent() -> str:
    return (datetime.now(UTC) - timedelta(days=10)).strftime("%Y-%m-%d")


def _stale() -> str:
    return (datetime.now(UTC) - timedelta(days=400)).strftime("%Y-%m-%d")


def _since_six_months() -> Timestamp:
    return Timestamp(datetime.now(UTC) - timedelta(days=180))


@respx.mock
def test_search_returns_filings_with_first_sale_and_officers() -> None:
    respx.get(SEARCH_ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            json={
                "hits": {
                    "hits": [
                        {
                            "_id": "0001234567-25-000001:primary_doc.xml",
                            "_source": {
                                "adsh": "0001234567-25-000001",
                                "ciks": ["0001234567"],
                                "file_date": _recent(),
                                "form": "D",
                                "display_names": ["Acme Newco Inc. (CIK 0001234567)"],
                            },
                        }
                    ]
                }
            },
        )
    )
    respx.get(
        "https://www.sec.gov/Archives/edgar/data/1234567/000123456725000001/primary_doc.xml"
    ).mock(return_value=httpx.Response(200, text=_PRIMARY_DOC))

    filings = _fetcher().search_form_d("Roelof", "Botha", _since_six_months())
    assert len(filings) == 1
    f = filings[0]
    assert f.accession_number == "0001234567-25-000001"
    assert f.issuer_name == "Acme Newco Inc."
    assert f.raise_amount == 5_000_000
    assert f.executive_officers == ("Jane Founder",)
    assert f.date_of_first_sale is not None
    assert f.date_of_first_sale.iso().startswith("2025-01-10")
    assert f.source_url.value.endswith("-index.htm")


@respx.mock
def test_yet_to_occur_returns_none_date() -> None:
    respx.get(SEARCH_ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            json={
                "hits": {
                    "hits": [
                        {
                            "_id": "0009999999-25-000007:primary_doc.xml",
                            "_source": {
                                "adsh": "0009999999-25-000007",
                                "ciks": ["0009999999"],
                                "file_date": _recent(),
                                "form": "D/A",
                                "display_names": ["StealthCo"],
                            },
                        }
                    ]
                }
            },
        )
    )
    respx.get(
        "https://www.sec.gov/Archives/edgar/data/9999999/000999999925000007/primary_doc.xml"
    ).mock(return_value=httpx.Response(200, text=_PRIMARY_DOC_YET_TO_OCCUR))

    filings = _fetcher().search_form_d("Pat", "Promoter", _since_six_months())
    assert len(filings) == 1
    assert filings[0].form_type == "D/A"
    assert filings[0].date_of_first_sale is None
    assert filings[0].executive_officers == ("Pat Promoter",)


@respx.mock
def test_pooled_vehicle_issuers_are_dropped() -> None:
    respx.get(SEARCH_ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            json={
                "hits": {
                    "hits": [
                        {
                            "_id": "0000111111-25-000001:primary_doc.xml",
                            "_source": {
                                "adsh": "0000111111-25-000001",
                                "ciks": ["0000111111"],
                                "file_date": _recent(),
                                "display_names": ["Acme Capital Fund III, LP"],
                            },
                        },
                        {
                            "_id": "0000222222-25-000001:primary_doc.xml",
                            "_source": {
                                "adsh": "0000222222-25-000001",
                                "ciks": ["0000222222"],
                                "file_date": _recent(),
                                "display_names": ["Brand X SPV"],
                            },
                        },
                        {
                            "_id": "0000333333-25-000001:primary_doc.xml",
                            "_source": {
                                "adsh": "0000333333-25-000001",
                                "ciks": ["0000333333"],
                                "file_date": _recent(),
                                "display_names": ["Real Newco Inc."],
                            },
                        },
                    ]
                }
            },
        )
    )
    respx.get(
        "https://www.sec.gov/Archives/edgar/data/333333/000033333325000001/primary_doc.xml"
    ).mock(return_value=httpx.Response(200, text=_PRIMARY_DOC))

    filings = _fetcher().search_form_d("Roelof", "Botha", _since_six_months())
    assert [f.issuer_name for f in filings] == ["Real Newco Inc."]


@respx.mock
def test_pagination_breaks_when_file_date_older_than_window() -> None:
    # Single page with a recent hit followed by a stale hit; the stale
    # one must trigger termination, not be persisted.
    respx.get(SEARCH_ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            json={
                "hits": {
                    "hits": [
                        {
                            "_id": "0001234567-25-000010:primary_doc.xml",
                            "_source": {
                                "adsh": "0001234567-25-000010",
                                "ciks": ["0001234567"],
                                "file_date": _recent(),
                                "display_names": ["RecentCo"],
                            },
                        },
                        {
                            "_id": "0001234567-24-000099:primary_doc.xml",
                            "_source": {
                                "adsh": "0001234567-24-000099",
                                "ciks": ["0001234567"],
                                "file_date": _stale(),
                                "display_names": ["AncientCo"],
                            },
                        },
                    ]
                }
            },
        )
    )
    respx.get(
        "https://www.sec.gov/Archives/edgar/data/1234567/000123456725000010/primary_doc.xml"
    ).mock(return_value=httpx.Response(200, text=_PRIMARY_DOC))

    filings = _fetcher().search_form_d("Roelof", "Botha", _since_six_months())
    issuers = [f.issuer_name for f in filings]
    assert "RecentCo" in issuers
    assert "AncientCo" not in issuers


@respx.mock
def test_search_handles_missing_primary_doc() -> None:
    respx.get(SEARCH_ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            json={
                "hits": {
                    "hits": [
                        {
                            "_id": "0001234567-25-000002:primary_doc.xml",
                            "_source": {
                                "adsh": "0001234567-25-000002",
                                "ciks": ["0001234567"],
                                "file_date": _recent(),
                                "display_names": ["MysteryCo"],
                            },
                        }
                    ]
                }
            },
        )
    )
    respx.get(
        "https://www.sec.gov/Archives/edgar/data/1234567/000123456725000002/primary_doc.xml"
    ).mock(return_value=httpx.Response(404))

    filings = _fetcher().search_form_d("Mary", "Meeker", _since_six_months())
    assert len(filings) == 1
    assert filings[0].issuer_name == "MysteryCo"
    assert filings[0].raise_amount is None
    assert filings[0].executive_officers == ()
    assert filings[0].date_of_first_sale is None
