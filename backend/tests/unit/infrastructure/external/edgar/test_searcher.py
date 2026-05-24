from datetime import date

import httpx
import pytest

from deal_flow.infrastructure.external.edgar.searcher import EdgarFullTextSearcher


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


def test_constructor_rejects_blank_user_agent(tmp_path):
    with pytest.raises(ValueError):
        EdgarFullTextSearcher(user_agent=" ", cache_dir=tmp_path)


def test_normalizes_hit_and_sends_required_params(tmp_path):
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            json=_page(
                1,
                [_hit(
                    adsh="0001483900-10-000004",
                    cik="0001483900",
                    issuer_display="Mixed Media Labs, Inc.  (CIK 0001483900)",
                    file_date="2010-11-16",
                )],
            ),
        )

    hits = _build(tmp_path, handler).search_form_d(
        query='"Marc Andreessen"', start=date(2010, 1, 1), end=date(2010, 12, 31)
    )

    assert hits == [{
        "accession_number": "0001483900-10-000004",
        "issuer_name": "Mixed Media Labs, Inc.",
        "issuer_cik": "0001483900",
        "filed_at": "2010-11-16",
        "url": "https://www.sec.gov/Archives/edgar/data/1483900/000148390010000004/0001483900-10-000004-index.htm",
    }]
    params = dict(captured[0].url.params)
    assert params == {
        "q": '"Marc Andreessen"',
        "forms": "D",
        "dateRange": "custom",
        "startdt": "2010-01-01",
        "enddt": "2010-12-31",
        "from": "0",
    }


def test_paginates_until_exhausted(tmp_path, monkeypatch):
    import deal_flow.infrastructure.external.edgar.searcher as mod
    monkeypatch.setattr(mod, "_INTER_PAGE_DELAY_S", 0)

    pages = [
        _page(150, [_hit(f"0000000000-25-{i:06d}", "0000000001", "Acme  (CIK 0000000001)", "2026-01-01") for i in range(100)]),
        _page(150, [_hit(f"0000000000-25-{i:06d}", "0000000001", "Acme  (CIK 0000000001)", "2026-01-01") for i in range(50)]),
    ]
    offsets: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        offsets.append(dict(request.url.params)["from"])
        return httpx.Response(200, json=pages[len(offsets) - 1])

    hits = _build(tmp_path, handler).search_form_d(
        query='"X"', start=date(2026, 1, 1), end=date(2026, 5, 24)
    )

    assert len(hits) == 150
    assert offsets == ["0", "100"]


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
