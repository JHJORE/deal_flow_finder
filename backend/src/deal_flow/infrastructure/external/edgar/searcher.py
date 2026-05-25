import time
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from typing import Any

import httpx

from deal_flow.application.ports.services.sec_filing_searcher import (
    SecFilingSearcher,
)
from deal_flow.infrastructure.cache.file_cache import FileCache

_ENDPOINT = "https://efts.sec.gov/LATEST/search-index"
_ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
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
        for hit in hits:
            hit.update(self._fetch_filing_detail(hit["issuer_cik"], hit["accession_number"]))
        self._cache.write(key, {"hits": hits})
        return hits

    def fetch_primary_doc(self, accession_number: str, cik: str) -> dict:
        """Fetch and parse a Form D primary_doc.xml. Cached like search."""
        if not accession_number or not cik:
            return _empty_primary_doc()
        key = FileCache.key_for(
            "edgar.primary_doc", adsh=accession_number, cik=cik
        )
        if not self._refresh:
            cached = self._cache.read(key)
            if cached is not None:
                return cached["payload"]

        url = (
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
            f"{accession_number.replace('-', '')}/primary_doc.xml"
        )
        resp = self._client.get(url, headers={"Accept": "application/xml"})
        resp.raise_for_status()
        time.sleep(_INTER_PAGE_DELAY_S)
        parsed = _parse_primary_doc(resp.text)
        self._cache.write(key, {"payload": parsed})
        return parsed

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

    def _fetch_filing_detail(self, cik: str, accession: str) -> dict:
        if not cik or not accession:
            return _empty_detail()
        key = FileCache.key_for("edgar.filing_detail", accession=accession)
        if not self._refresh:
            cached = self._cache.read(key)
            if cached is not None:
                return cached
        url = (
            f"{_ARCHIVES}/{int(cik)}/{accession.replace('-', '')}/primary_doc.xml"
        )
        response = self._client.get(url)
        response.raise_for_status()
        detail = _parse_form_d_xml(response.content)
        self._cache.write(key, detail)
        time.sleep(_INTER_PAGE_DELAY_S)
        return detail


def _empty_primary_doc() -> dict:
    return {
        "issuer_name": "",
        "related_persons": [],
        "industry_group": None,
        "is_pooled_investment_fund": False,
    }


def _parse_primary_doc(xml_text: str) -> dict:
    """Parse Form D primary_doc.xml (schema X0708, no namespace)."""
    root = ET.fromstring(xml_text)
    related: list[dict] = []
    for info in root.findall("relatedPersonsList/relatedPersonInfo"):
        related.append({
            "first_name": _text_at(info, "relatedPersonName/firstName"),
            "last_name": _text_at(info, "relatedPersonName/lastName"),
            "relationships": [
                (r.text or "").strip()
                for r in info.findall("relatedPersonRelationshipList/relationship")
                if r.text
            ],
            "relationship_clarification": _text_at(info, "relationshipClarification") or None,
        })
    return {
        "issuer_name": _text_at(root, "primaryIssuer/entityName"),
        "related_persons": related,
        "industry_group": _text_at(root, "offeringData/industryGroup/industryGroupType") or None,
        "is_pooled_investment_fund": _text_at(
            root, "offeringData/typesOfSecuritiesOffered/isPooledInvestmentFundType"
        ).lower() == "true",
    }


def _text_at(node: ET.Element, path: str) -> str:
    found = node.find(path)
    return (found.text or "").strip() if found is not None and found.text else ""


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
            f"{_ARCHIVES}/{int(cik)}/"
            f"{adsh.replace('-', '')}/{adsh}-index.htm"
            if cik and adsh
            else ""
        ),
    }


def _empty_detail() -> dict:
    return {
        "total_offering_amount": None,
        "total_amount_sold": None,
        "related_persons": [],
    }


def _parse_form_d_xml(xml_bytes: bytes) -> dict:
    root = ET.fromstring(xml_bytes)
    detail = _empty_detail()

    amounts = root.find("offeringData/offeringSalesAmounts")
    if amounts is not None:
        detail["total_offering_amount"] = _to_int(
            _text(amounts.find("totalOfferingAmount"))
        )
        detail["total_amount_sold"] = _to_int(
            _text(amounts.find("totalAmountSold"))
        )

    persons: list[dict] = []
    for person in root.findall("relatedPersonsList/relatedPersonInfo"):
        first = _text(person.find("relatedPersonName/firstName")) or ""
        last = _text(person.find("relatedPersonName/lastName")) or ""
        relationships = [
            (r.text or "").strip()
            for r in person.findall("relatedPersonRelationshipList/relationship")
            if r.text and r.text.strip()
        ]
        persons.append(
            {
                "first_name": first,
                "last_name": last,
                "relationships": relationships,
                "relationship_clarification": _text(
                    person.find("relationshipClarification")
                ),
            }
        )
    detail["related_persons"] = persons
    return detail


def _text(node: ET.Element | None) -> str | None:
    if node is None or node.text is None:
        return None
    stripped = node.text.strip()
    return stripped or None


def _to_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None
