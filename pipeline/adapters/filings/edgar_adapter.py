"""SEC EDGAR adapter for the ``FilingFetcher`` port.

EDGAR exposes a full-text search at ``efts.sec.gov/LATEST/search-index``.
We query for Form D filings where the investor alias appears in the
filing text, then fetch each hit's structured ``primary_doc.xml`` to
extract issuer, raise amount, named investors, and filing date.

Real-world Form D parsing is messy (XML with optional fields, money
fields that are strings, investors listed under different element paths).
We're conservative: any field that fails to parse becomes ``None`` rather
than failing the whole filing.
"""

from __future__ import annotations

import re
from typing import Any
from xml.etree import ElementTree as ET

import httpx

from pipeline.adapters._common.http import request_with_retry
from pipeline.entities.errors import FetchError, ParseError, ValidationError
from pipeline.entities.models import Filing
from pipeline.entities.value_objects import Cik, Timestamp, Url

SEARCH_ENDPOINT = "https://efts.sec.gov/LATEST/search-index"
FILING_BASE = "https://www.sec.gov/Archives/edgar/data"


class EdgarFilingFetcher:
    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def search_form_d(self, investor_alias: str, since: Timestamp) -> list[Filing]:
        resp = request_with_retry(
            lambda: self._client.get(
                SEARCH_ENDPOINT,
                params={
                    "q": f'"{investor_alias}"',
                    "dateRange": "custom",
                    "startdt": since.value.strftime("%Y-%m-%d"),
                    "enddt": Timestamp.now().value.strftime("%Y-%m-%d"),
                    "forms": "D",
                },
            )
        )
        try:
            payload = resp.json()
        except ValueError as exc:
            raise ParseError(f"edgar search returned non-json: {exc}") from exc

        hits = (payload.get("hits", {}) or {}).get("hits", [])
        out: list[Filing] = []
        for hit in hits:
            filing = self._build_filing(hit, investor_alias)
            if filing is not None:
                out.append(filing)
        return out

    # ------------------------------------------------------------------ #

    def _build_filing(self, hit: dict[str, Any], investor_alias: str) -> Filing | None:
        source = hit.get("_source") or {}
        # EDGAR's _id is the accession plus a ":<filename>" suffix
        # (e.g. "0001234567-25-000001:primary_doc.xml"). _source.adsh is the
        # bare accession we actually want; fall back to splitting _id if it's
        # the only thing present.
        accession = source.get("adsh")
        if not accession:
            raw_id = hit.get("_id") or ""
            accession = raw_id.split(":", 1)[0] if raw_id else ""
        if not accession:
            return None

        ciks = source.get("ciks") or []
        cik_int = _first_int(ciks)
        if cik_int is None:
            return None
        try:
            cik = Cik(cik_int)
        except ValidationError:
            return None

        filing_date_raw = source.get("file_date") or source.get("filed")
        try:
            filing_date = Timestamp.from_iso(str(filing_date_raw))
        except ValidationError:
            return None

        accession_clean = accession.replace("-", "")
        # EDGAR convention: .htm (not .html) for the per-filing index page.
        archive_url_str = f"{FILING_BASE}/{cik.value}/{accession_clean}/{accession}-index.htm"
        try:
            source_url = Url(archive_url_str)
        except ValidationError:
            return None

        issuer = source.get("display_names", [None])[0] or source.get("entity") or "Unknown"
        if isinstance(issuer, str):
            issuer = re.sub(r"\s*\(.*?\)\s*$", "", issuer).strip() or "Unknown"

        # Best-effort raise amount + investors from the primary doc, if available.
        raise_amount, named_investors = self._fetch_form_d_details(cik, accession)
        if not named_investors:
            named_investors = (investor_alias,)

        try:
            return Filing(
                cik=cik,
                issuer_name=str(issuer),
                raise_amount=raise_amount,
                named_investors=named_investors,
                filing_date=filing_date,
                form_type="D",
                accession_number=accession,
                source_url=source_url,
            )
        except ValidationError:
            return None

    def _fetch_form_d_details(self, cik: Cik, accession: str) -> tuple[int | None, tuple[str, ...]]:
        accession_clean = accession.replace("-", "")
        primary_doc = f"{FILING_BASE}/{cik.value}/{accession_clean}/primary_doc.xml"
        try:
            resp = request_with_retry(lambda: self._client.get(primary_doc))
        except FetchError:
            return None, ()
        if resp.status_code != 200 or not resp.text:
            return None, ()

        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError:
            return None, ()

        amount = _find_text(root, ".//{*}totalOfferingAmount")
        raise_amount = None
        if amount is not None:
            try:
                raise_amount = int(float(amount))
            except ValueError:
                raise_amount = None

        investors: list[str] = []
        for node in root.iter():
            tag = node.tag.split("}", 1)[-1]
            if tag.lower() == "relatedpersonname":
                given = _find_text(node, "{*}relatedPersonFirstName") or ""
                family = _find_text(node, "{*}relatedPersonLastName") or ""
                full = f"{given} {family}".strip()
                if full:
                    investors.append(full)
            elif tag.lower() == "issuername" and node.text:
                # Some filings duplicate issuer; ignored for investors.
                continue
            elif tag.lower() == "investmentfundname" and node.text:
                investors.append(node.text.strip())

        return raise_amount, tuple(dict.fromkeys(investors))  # de-dup preserving order


def _first_int(values: list[Any]) -> int | None:
    for v in values:
        try:
            return int(v)
        except (TypeError, ValueError):
            continue
    return None


def _find_text(node: ET.Element, path: str) -> str | None:
    found = node.find(path)
    if found is None or found.text is None:
        return None
    return found.text.strip() or None
