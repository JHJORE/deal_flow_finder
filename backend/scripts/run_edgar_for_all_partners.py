"""Run the EDGAR Form D pipeline over every partner of every firm in firms.yaml.

Writes one curated file per firm:
``backend/.outputs/firms/{firm_domain}/board_seats.json``.

Partner names come from the existing Firecrawl cache (no SDK init, no API
key required) — so this script is free to run as long as the firm's team
page has been crawled at least once.
"""

from __future__ import annotations

import html as html_lib
import json
import re
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import httpx

from deal_flow.application.use_cases.search_partner_form_d_filings import (
    SearchPartnerFormDFilings,
    SearchPartnerFormDFilingsInput,
)
from deal_flow.domain.value_objects.date_range import DateRange
from deal_flow.infrastructure.config.settings import get_settings
from deal_flow.infrastructure.external.edgar.searcher import EdgarFullTextSearcher
from deal_flow.infrastructure.external.firms_registry import FirmSources, load_registry
from deal_flow.infrastructure.persistence.file_board_seat_log import FileBoardSeatLog


def _names_from_payload(
    payload_url: str, attribute: str, role_filter: str | None
) -> list[str]:
    """Free urllib scrape of an inline data-payload attribute (a16z pattern)."""
    req = urllib.request.Request(payload_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    m = re.search(rf'{re.escape(attribute)}="([^"]+)"', raw)
    if not m:
        return []
    data = json.loads(html_lib.unescape(m.group(1)))
    members = data.get("members") if isinstance(data, dict) else data
    out: list[str] = []
    for member in members or []:
        if role_filter and role_filter not in (member.get("role_display") or ""):
            continue
        name = (member.get("name") or "").strip()
        if name:
            out.append(name)
    return out


def _names_from_cache(firecrawl_dir: Path, sources: FirmSources) -> list[str]:
    """Read partner-listing payloads cached under ``firecrawl_dir`` and
    return deduped partner names for the URLs this firm uses.
    """
    wanted_urls = {tu.url for tu in sources.team_urls}
    if sources.team_payload_url:
        wanted_urls.add(sources.team_payload_url)
    names: list[str] = []
    seen: set[str] = set()
    for cache_file in firecrawl_dir.glob("*.json"):
        try:
            doc = json.loads(cache_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if doc.get("op") != "scrape":
            continue
        url = (doc.get("inputs") or {}).get("url")
        if url not in wanted_urls:
            continue
        for p in (doc.get("payload") or {}).get("partners") or []:
            n = (p.get("name") or "").strip()
            if n and n.lower() not in seen:
                names.append(n)
                seen.add(n.lower())
    return names


def main() -> None:
    s = get_settings()
    registry = load_registry()

    searcher = EdgarFullTextSearcher(
        user_agent=s.sec_user_agent,
        cache_dir=s.sec_cache_dir / ".cache",
        refresh=s.sec_cache_refresh,
    )
    window = DateRange(start=date.today() - timedelta(days=365), end=date.today())

    grand_total = 0
    for domain, sources in registry.items():
        print(f"\n=== {domain} ===")
        partners_path = s.output_dir / "firms" / domain / "partners.json"
        if partners_path.exists():
            names = json.loads(partners_path.read_text(encoding="utf-8"))
            source_label = f"from {partners_path}"
        else:
            if sources.team_payload_url:
                names = _names_from_payload(
                    sources.team_payload_url,
                    sources.team_payload_attribute or "data-payload",
                    sources.team_payload_role_filter,
                )
            else:
                names = _names_from_cache(s.firecrawl_cache_dir, sources)
            if names:
                partners_path.parent.mkdir(parents=True, exist_ok=True)
                partners_path.write_text(
                    json.dumps(names, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                source_label = f"seeded → {partners_path}"
            else:
                source_label = "(none found)"
        if not names:
            print(f"  ! no partners resolved for {domain} — skipped")
            continue
        print(f"  {len(names)} partners {source_label}")

        out_path = s.output_dir / "firms" / domain / "board_seats.json"
        if out_path.exists():
            out_path.unlink()
        log = FileBoardSeatLog(path=out_path)
        search_filings = SearchPartnerFormDFilings(searcher=searcher, log=log)

        firm_total = 0
        skipped = 0
        for name in names:
            try:
                signal = search_filings.execute(
                    SearchPartnerFormDFilingsInput(
                        partner_name=name, date_range=window
                    )
                )
            except httpx.HTTPStatusError as e:
                print(f"  ! {name}: EDGAR {e.response.status_code} — skipped")
                skipped += 1
                continue
            if signal.filings:
                firm_total += len(signal.filings)
                for f in signal.filings:
                    sold = (
                        f"${f.total_amount_sold:,}"
                        if f.total_amount_sold
                        else "n/a"
                    )
                    print(f"  ✓ {name}  →  {f.filed_at}  {f.issuer_name}  {sold}")
        print(
            f"  {firm_total} board-seat filings ({skipped} skipped)  →  {out_path}"
        )
        grand_total += firm_total

    print(f"\n=== TOTAL: {grand_total} board-seat filings across all firms ===")


if __name__ == "__main__":
    main()
