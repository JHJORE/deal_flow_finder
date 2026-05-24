import time
from datetime import date
from pathlib import Path
from typing import Any

import httpx

from deal_flow.application.ports.services.sec_filing_searcher import (
    SecFilingSearcher,
)
from deal_flow.infrastructure.cache.file_cache import FileCache

_ENDPOINT = "https://efts.sec.gov/LATEST/search-index"
_PAGE_SIZE = 100
_INTER_PAGE_DELAY_S = 0.1


class EdgarFullTextSearcher(SecFilingSearcher):
    """Free EDGAR full-text search. Endpoint is undocumented but stable;
    response is Elasticsearch-shaped. EDGAR blocks requests lacking a
    contact-bearing User-Agent header.
    """

    def __init__(self, user_agent: str, cache_dir: Path, refresh: bool = False) -> None:
        if not user_agent.strip():
            raise ValueError(
                "SEC_USER_AGENT is required. Set it to 'Your Name your@email.com'."
            )
        self._cache = FileCache(cache_dir)
        self._refresh = refresh
        self._client = httpx.Client(
            headers={"User-Agent": user_agent, "Accept": "application/json"},
            timeout=httpx.Timeout(30.0),
        )

    def search_form_d(self, query: str, start: date, end: date) -> list[dict]:
        key = FileCache.key_for(
            "edgar.search_form_d",
            query=query,
            start=start.isoformat(),
            end=end.isoformat(),
        )
        if not self._refresh:
            cached = self._cache.read(key)
            if cached is not None:
                return cached["hits"]

        hits = self._fetch_all(query, start, end)
        self._cache.write(key, {"hits": hits})
        return hits

    def _fetch_all(self, query: str, start: date, end: date) -> list[dict]:
        collected: list[dict] = []
        offset = 0
        while True:
            page = self._fetch_page(query, start, end, offset)
            raw = page["hits"]["hits"]
            collected.extend(_normalize(h) for h in raw)
            total = page["hits"]["total"]["value"]
            if len(raw) < _PAGE_SIZE or len(collected) >= total:
                return collected
            offset += _PAGE_SIZE
            time.sleep(_INTER_PAGE_DELAY_S)

    def _fetch_page(
        self, query: str, start: date, end: date, offset: int
    ) -> dict[str, Any]:
        response = self._client.get(
            _ENDPOINT,
            params={
                "q": query,
                "forms": "D",
                "dateRange": "custom",
                "startdt": start.isoformat(),
                "enddt": end.isoformat(),
                "from": offset,
            },
        )
        response.raise_for_status()
        return response.json()


def _normalize(raw_hit: dict) -> dict:
    src = raw_hit.get("_source") or {}
    adsh = src.get("adsh") or ""
    cik = (src.get("ciks") or [""])[0]
    display = (src.get("display_names") or [""])[0]
    # Display name is "Issuer Name  (CIK XXXXXXXXXX)" — strip the suffix.
    head, sep, _ = display.rpartition("(CIK")
    issuer_name = head.strip() if sep else display.strip()
    return {
        "accession_number": adsh,
        "issuer_name": issuer_name,
        "issuer_cik": cik,
        "filed_at": src.get("file_date") or "",
        "url": (
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
            f"{adsh.replace('-', '')}/{adsh}-index.htm"
            if cik and adsh
            else ""
        ),
    }
