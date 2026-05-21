from __future__ import annotations

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
  </offeringData>
  <relatedPersonsList>
    <relatedPersonInfo>
      <relatedPersonName>
        <relatedPersonFirstName>Roelof</relatedPersonFirstName>
        <relatedPersonLastName>Botha</relatedPersonLastName>
      </relatedPersonName>
    </relatedPersonInfo>
  </relatedPersonsList>
</edgarSubmission>
"""


@respx.mock
def test_search_returns_filings() -> None:
    # EDGAR sends _id as "<accession>:<filename>". We must use _source.adsh
    # to recover the bare accession, otherwise URL construction breaks.
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
                                "file_date": "2025-01-15",
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

    filings = _fetcher().search_form_d("Sequoia Capital", Timestamp.now())
    assert len(filings) == 1
    assert filings[0].accession_number == "0001234567-25-000001"
    assert filings[0].issuer_name == "Acme Newco Inc."
    assert filings[0].raise_amount == 5_000_000
    assert "Roelof Botha" in filings[0].named_investors
    # Filing index URL should end in .htm per EDGAR convention.
    assert filings[0].source_url.value.endswith("-index.htm")


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
                                "file_date": "2025-01-20",
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

    filings = _fetcher().search_form_d("a16z", Timestamp.now())
    assert len(filings) == 1
    assert filings[0].issuer_name == "MysteryCo"
    assert filings[0].raise_amount is None
    assert filings[0].named_investors == ("a16z",)
