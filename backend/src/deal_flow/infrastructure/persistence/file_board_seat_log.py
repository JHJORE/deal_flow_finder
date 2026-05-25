import json
from pathlib import Path

from deal_flow.application.ports.repositories.board_seat_log import BoardSeatLog
from deal_flow.domain.entities.partner_form_d_signal import PartnerFormDSignal


class FileBoardSeatLog(BoardSeatLog):
    """JSON file holding the curated, Director-filtered Form D records.

    Each row carries everything we want to click through to: issuer, amounts,
    related persons, EDGAR URL. Deduped by (partner_name, accession_number).
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, signal: PartnerFormDSignal) -> None:
        rows = self._load()
        seen = {(r["partner_name"], r["accession_number"]) for r in rows}
        for filing in signal.filings:
            key = (signal.partner_name, filing.accession_number)
            if key in seen:
                continue
            rows.append(
                {
                    "partner_name": signal.partner_name,
                    "accession_number": filing.accession_number,
                    "issuer_name": filing.issuer_name,
                    "issuer_cik": filing.issuer_cik,
                    "filed_at": filing.filed_at.isoformat(),
                    "url": filing.url,
                    "total_offering_amount": filing.total_offering_amount,
                    "total_amount_sold": filing.total_amount_sold,
                    "related_persons": [
                        {
                            "first_name": p.first_name,
                            "last_name": p.last_name,
                            "relationships": list(p.relationships),
                            "relationship_clarification": p.relationship_clarification,
                        }
                        for p in filing.related_persons
                    ],
                }
            )
            seen.add(key)
        self._path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    def _load(self) -> list[dict]:
        if not self._path.exists():
            return []
        return json.loads(self._path.read_text(encoding="utf-8"))
