"""SEC EDGAR adapter for the ``FilingFetcher`` port.

EDGAR exposes a full-text search at ``efts.sec.gov/LATEST/search-index``.
We query Form D (and D/A) filings where a scraped GP partner appears as
a "Director" on Item 3 (Related Persons), then fetch each hit's
``primary_doc.xml`` to recover the true wire date (``dateOfFirstSale``),
the raise amount, and the Executive Officer / Promoter names (the
founders we use for shell-vs-brand entity resolution downstream).

Real-world Form D parsing is messy (namespaced XML, optional fields,
choice elements like ``<value>`` vs ``<yetToOccur>``). We're conservative:
any field that fails to parse becomes ``None`` rather than failing the
whole filing.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any
from xml.etree import ElementTree as ET

import httpx

from pipeline.adapters._common.http import request_with_retry
from pipeline.entities.errors import FetchError, ParseError, ValidationError
from pipeline.entities.models import Filing
from pipeline.entities.value_objects import Cik, Timestamp, Url

SEARCH_ENDPOINT = "https://efts.sec.gov/LATEST/search-index"
FILING_BASE = "https://www.sec.gov/Archives/edgar/data"

# SEC EDGAR fair-use cap is 10 req/s. 0.15s between calls keeps headroom.
_REQUEST_SPACING_SECONDS = 0.15
# EDGAR returns 10 hits per page by default; the search API caps `start`
# offset increments at 100, so we advance the cursor by 100 per page.
_PAGE_SIZE = 100
# Issuer names containing these tokens are pooled vehicles (fund-of-funds,
# SPVs, management entities), not portfolio companies — drop them before
# we spend an HTTP round trip fetching the primary doc.
_ISSUER_DROP_TOKENS = ("fund", "partners", "management", "spv")

logger = logging.getLogger(__name__)


class EdgarFilingFetcher:
    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def search_form_d(
        self, first_name: str, last_name: str, since: Timestamp
    ) -> list[Filing]:
        query = f'"{first_name}" AND "{last_name}" AND "Director"'
        startdt = since.value.strftime("%Y-%m-%d")
        enddt = Timestamp.now().value.strftime("%Y-%m-%d")

        out: list[Filing] = []
        seen_accessions: set[str] = set()
        start = 0
        stop = False
        while not stop:
            current_start = start
            resp = request_with_retry(
                lambda: self._client.get(
                    SEARCH_ENDPOINT,
                    params={
                        "q": query,
                        "dateRange": "custom",
                        "startdt": startdt,
                        "enddt": enddt,
                        "forms": "D,D/A",
                        "from": current_start,
                    },
                )
            )
            time.sleep(_REQUEST_SPACING_SECONDS)
            try:
                payload = resp.json()
            except ValueError as exc:
                raise ParseError(f"edgar search returned non-json: {exc}") from exc

            hits = (payload.get("hits", {}) or {}).get("hits", [])
            if not hits:
                break

            for hit in hits:
                # EDGAR returns newest-first; break the loop as soon as we
                # cross the 6-month boundary so we don't paginate forever.
                file_date_raw = (hit.get("_source") or {}).get("file_date") or (
                    hit.get("_source") or {}
                ).get("filed")
                try:
                    file_ts = Timestamp.from_iso(str(file_date_raw))
                except ValidationError:
                    continue
                if file_ts.value < since.value:
                    stop = True
                    break

                filing = self._build_filing(hit)
                if filing is None:
                    continue
                if filing.accession_number in seen_accessions:
                    continue
                seen_accessions.add(filing.accession_number)
                out.append(filing)

            if len(hits) < _PAGE_SIZE:
                break
            start += _PAGE_SIZE

        return out

    # ------------------------------------------------------------------ #

    def _build_filing(self, hit: dict[str, Any]) -> Filing | None:
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

        # Pre-filter pooled-vehicle issuers before paying for the XML.
        if _is_pooled_vehicle(str(issuer)):
            return None

        form_type = str(source.get("form") or "D")

        raise_amount, executive_officers, date_of_first_sale = self._fetch_form_d_details(
            cik, accession
        )

        try:
            return Filing(
                cik=cik,
                issuer_name=str(issuer),
                raise_amount=raise_amount,
                filing_date=filing_date,
                form_type=form_type,
                accession_number=accession,
                source_url=source_url,
                date_of_first_sale=date_of_first_sale,
                executive_officers=executive_officers,
            )
        except ValidationError:
            return None

    def _fetch_form_d_details(
        self, cik: Cik, accession: str
    ) -> tuple[int | None, tuple[str, ...], Timestamp | None]:
        accession_clean = accession.replace("-", "")
        primary_doc = f"{FILING_BASE}/{cik.value}/{accession_clean}/primary_doc.xml"
        try:
            resp = request_with_retry(lambda: self._client.get(primary_doc))
        except FetchError:
            return None, (), None
        time.sleep(_REQUEST_SPACING_SECONDS)
        if resp.status_code != 200 or not resp.text:
            return None, (), None

        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError:
            return None, (), None

        amount = _find_text(root, ".//{*}totalOfferingAmount")
        raise_amount: int | None = None
        if amount is not None:
            try:
                raise_amount = int(float(amount))
            except ValueError:
                raise_amount = None

        date_of_first_sale = _parse_date_of_first_sale(root)
        executive_officers = _parse_executive_officers(root)

        return raise_amount, executive_officers, date_of_first_sale


def _parse_date_of_first_sale(root: ET.Element) -> Timestamp | None:
    """Item 7 wraps a choice element: ``<value>`` for closed sales,
    ``<yetToOccur/>`` while the offering is still open."""
    node = root.find(".//{*}dateOfFirstSale")
    if node is None:
        return None
    if node.find("{*}yetToOccur") is not None:
        return None
    value = _find_text(node, "{*}value")
    if value is None:
        return None
    try:
        return Timestamp.from_iso(value)
    except ValidationError:
        return None


def _parse_executive_officers(root: ET.Element) -> tuple[str, ...]:
    """Extract founder names from Item 3 Related Persons.

    Returns names whose ``<relationship>`` is ``Executive Officer`` or
    ``Promoter`` — the human anchors we use to resolve a stealth shell
    name back to a known portfolio company. Directors are ignored here
    because they're the GP we searched for (already attributed via
    ``PartnerFilingHit.partner``).
    """
    officers: list[str] = []

    persons_list = root.find(".//{*}relatedPersonsList")
    if persons_list is None:
        return ()

    for info in persons_list.findall("{*}relatedPersonInfo"):
        relationships = {
            (r.text or "").strip().lower()
            for r in info.findall(".//{*}relationship")
            if r.text
        }
        if not ({"executive officer", "promoter"} & relationships):
            continue
        name_node = info.find("{*}relatedPersonName")
        if name_node is None:
            continue
        first = _find_text(name_node, "{*}relatedPersonFirstName") or ""
        last = _find_text(name_node, "{*}relatedPersonLastName") or ""
        full = f"{first} {last}".strip()
        if full:
            officers.append(full)

    return tuple(dict.fromkeys(officers))


def _is_pooled_vehicle(issuer: str) -> bool:
    lowered = issuer.lower()
    return any(token in lowered for token in _ISSUER_DROP_TOKENS)


def _first_int(values: list[Any]) -> int | None:
    for v in values:
        try:
            return int(v)
        except (TypeError, ValueError):
            continue
    return None


def _find_text(node: ET.Element | None, path: str) -> str | None:
    if node is None:
        return None
    found = node.find(path)
    if found is None or found.text is None:
        return None
    return found.text.strip() or None
