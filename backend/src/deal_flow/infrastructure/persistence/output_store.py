"""Write-only JSON sidecar for processed domain entities.

One file per business key (firm / partner). Used purely so a human (or
another tool) can read ``backend/.outputs/firms/a16z.com/partners.json``
and see the assembled ``Partner`` records with every field — including
``photo_url``, ``education``, ``prior_experience`` — without spelunking the
hash-keyed adapter caches.

Not a cache. The adapter-level ``FileCache`` already handles re-use of
upstream API responses; this layer only persists the *result* of the use
case for inspection.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


class _Encoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if is_dataclass(o) and not isinstance(o, type):
            return asdict(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, tuple):
            return list(o)
        if isinstance(o, Path):
            return str(o)
        return super().default(o)


class OutputStore:
    def __init__(self, base_dir: Path) -> None:
        self._dir = base_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def write(self, payload: Any, *parts: str) -> Path:
        path = self._dir.joinpath(*parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, cls=_Encoder, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-") or "unknown"
