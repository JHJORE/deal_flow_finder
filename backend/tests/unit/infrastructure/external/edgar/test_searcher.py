from datetime import date
from pathlib import Path

import httpx
import pytest

from deal_flow.infrastructure.external.edgar.searcher import (
    EdgarFullTextSearcher,
    _parse_form_d_xml,
)

FIXTURE = (
    Path(__file__).resolve().parents[4]
    / "fixtures"
    / "edgar"
    / "a16z_lsv_fund_ii_b.xml"
)

_EMPTY_FORM_D = b"<edgarSubmission></edgarSubmission>"


def _page(total: int, hits: list[dict]) -> dict:
    return {"hits": {"total": {"value": total, "relation": "eq"}, "hits": hits}}


def _hit(adsh: str, cik: str, issuer_display: str, file_date: str) -> dict:
    return {
        "_id": f"{adsh}:primary_doc.xml",
        "_source": {
            "adsh": adsh,
            "ciks": [cik],
            "display_names": [issuer_display],
            "file_date": file_date,
            "form": "D",
        },
    }


def _build(tmp_path, handler) -> EdgarFullTextSearcher:
    searcher = EdgarFullTextSearcher(user_agent="Test test@example.com", cache_dir=tmp_path)
    searcher._client = httpx.Client(transport=httpx.MockTransport(handler))
    return searcher


def _is_efts(request: httpx.Request) -> bool:
    return request.url.host == "efts.sec.gov"


def test_constructor_rejects_blank_user_agent(tmp_path):
    with pytest.raises(ValueError):
        EdgarFullTextSearcher(user_agent=" ", cache_dir=tmp_path)


def test_normalizes_hit_and_enriches_with_xml(tmp_path, monkeypatch):
    import deal_flow.infrastructure.external.edgar.searcher as mod
    monkeypatch.setattr(mod, "_INTER_PAGE_DELAY_S", 0)
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        if _is_efts(request):
            return httpx.Response(
                200,
                json=_page(
                    1,
                    [_hit(
                        adsh="0001829459-21-000001",
                        cik="0001829459",
                        issuer_display="Andreessen Horowitz LSV Fund II-B, L.P.  (CIK 0001829459)",
                        file_date="2021-02-23",
                    )],
                ),
            )
        return httpx.Response(200, content=FIXTURE.read_bytes())

    hits = _build(tmp_path, handler).search_form_d(
        query='"Marc Andreessen"', start=date(2020, 1, 1), end=date(2021, 12, 31)
    )

    assert len(hits) == 1
    hit = hits[0]
    assert hit["accession_number"] == "0001829459-21-000001"
    assert hit["issuer_name"] == "Andreessen Horowitz LSV Fund II-B, L.P."
    assert hit["issuer_cik"] == "0001829459"
    assert hit["filed_at"] == "2021-02-23"
    names = {(p["first_name"], p["last_name"]) for p in hit["related_persons"]}
    assert ("Marc", "Andreessen") in names
    assert ("Ben", "Horowitz") in names

    efts_params = dict(captured[0].url.params)
    assert efts_params == {
        "q": '"Marc Andreessen"',
        "forms": "D",
        "dateRange": "custom",
        "startdt": "2020-01-01",
        "enddt": "2021-12-31",
        "from": "0",
    }
    xml_request = next(r for r in captured if not _is_efts(r))
    assert str(xml_request.url) == (
        "https://www.sec.gov/Archives/edgar/data/1829459/"
        "000182945921000001/primary_doc.xml"
    )


def test_paginates_until_exhausted(tmp_path, monkeypatch):
    import deal_flow.infrastructure.external.edgar.searcher as mod
    monkeypatch.setattr(mod, "_INTER_PAGE_DELAY_S", 0)

    pages = [
        _page(150, [_hit(f"0000000000-25-{i:06d}", "0000000001", "Acme  (CIK 0000000001)", "2026-01-01") for i in range(100)]),
        _page(150, [_hit(f"0000000000-25-{i:06d}", "0000000001", "Acme  (CIK 0000000001)", "2026-01-01") for i in range(50)]),
    ]
    offsets: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if _is_efts(request):
            offsets.append(dict(request.url.params)["from"])
            return httpx.Response(200, json=pages[len(offsets) - 1])
        return httpx.Response(200, content=_EMPTY_FORM_D)

    hits = _build(tmp_path, handler).search_form_d(
        query='"X"', start=date(2026, 1, 1), end=date(2026, 5, 24)
    )

    assert len(hits) == 150
    assert offsets == ["0", "100"]


def test_fetch_primary_doc_parses_related_persons(tmp_path):
    xml = """<?xml version="1.0"?>
<edgarSubmission>
  <primaryIssuer><entityName>AH 2026 Fund, L.P.</entityName></primaryIssuer>
  <relatedPersonsList>
    <relatedPersonInfo>
      <relatedPersonName><firstName>Marc</firstName><lastName>Andreessen</lastName></relatedPersonName>
      <relatedPersonRelationshipList>
        <relationship>Executive Officer</relationship>
      </relatedPersonRelationshipList>
      <relationshipClarification>Managing member of GP</relationshipClarification>
    </relatedPersonInfo>
  </relatedPersonsList>
  <offeringData>
    <industryGroup><industryGroupType>Pooled Investment Fund</industryGroupType></industryGroup>
    <typesOfSecuritiesOffered><isPooledInvestmentFundType>true</isPooledInvestmentFundType></typesOfSecuritiesOffered>
  </offeringData>
</edgarSubmission>"""

    def handler(request):
        return httpx.Response(200, text=xml)

    doc = _build(tmp_path, handler).fetch_primary_doc(
        accession_number="0001104659-26-002089", cik="0002084463"
    )
    assert doc == {
        "issuer_name": "AH 2026 Fund, L.P.",
        "related_persons": [
            {
                "first_name": "Marc",
                "last_name": "Andreessen",
                "relationships": ["Executive Officer"],
                "relationship_clarification": "Managing member of GP",
            }
        ],
        "industry_group": "Pooled Investment Fund",
        "is_pooled_investment_fund": True,
    }


def test_cache_hit_skips_network(tmp_path):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json=_page(0, []))

    searcher = _build(tmp_path, handler)
    args = dict(query='"X"', start=date(2026, 1, 1), end=date(2026, 5, 24))
    searcher.search_form_d(**args)
    searcher.search_form_d(**args)
    assert calls["n"] == 1


def test_xml_fetch_cached_across_calls(tmp_path, monkeypatch):
    import deal_flow.infrastructure.external.edgar.searcher as mod
    monkeypatch.setattr(mod, "_INTER_PAGE_DELAY_S", 0)
    xml_calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if _is_efts(request):
            return httpx.Response(
                200,
                json=_page(
                    1,
                    [_hit(
                        adsh="0001829459-21-000001",
                        cik="0001829459",
                        issuer_display="Andreessen Horowitz LSV Fund II-B, L.P.  (CIK 0001829459)",
                        file_date="2021-02-23",
                    )],
                ),
            )
        xml_calls["n"] += 1
        return httpx.Response(200, content=FIXTURE.read_bytes())

    searcher = _build(tmp_path, handler)
    args = dict(query='"Marc Andreessen"', start=date(2020, 1, 1), end=date(2021, 12, 31))
    searcher.search_form_d(**args)
    # second call hits the search-index cache and therefore avoids both endpoints
    searcher.search_form_d(**args)
    assert xml_calls["n"] == 1


def test_parse_form_d_xml_extracts_related_persons_and_amounts():
    detail = _parse_form_d_xml(FIXTURE.read_bytes())

    assert detail["total_offering_amount"] == 67659196
    assert detail["total_amount_sold"] == 67659196

    persons = detail["related_persons"]
    assert len(persons) >= 2
    by_name = {(p["first_name"], p["last_name"]): p for p in persons}
    marc = by_name[("Marc", "Andreessen")]
    assert marc["relationships"] == ["Executive Officer"]
    assert marc["relationship_clarification"] == "Managing Member of the General Partner"


def test_parse_form_d_xml_handles_missing_related_persons():
    xml = b"""<?xml version="1.0"?>
    <edgarSubmission>
        <primaryIssuer><entityType>Corporation</entityType></primaryIssuer>
    </edgarSubmission>"""

    detail = _parse_form_d_xml(xml)

    assert detail["related_persons"] == []
    assert detail["total_offering_amount"] is None
    assert detail["total_amount_sold"] is None


def test_parse_form_d_xml_handles_non_numeric_offering_amount():
    xml = b"""<?xml version="1.0"?>
    <edgarSubmission>
        <offeringData>
            <offeringSalesAmounts>
                <totalOfferingAmount>Indefinite</totalOfferingAmount>
                <totalAmountSold>0</totalAmountSold>
            </offeringSalesAmounts>
        </offeringData>
    </edgarSubmission>"""

    detail = _parse_form_d_xml(xml)

    assert detail["total_offering_amount"] is None
    assert detail["total_amount_sold"] == 0
