"""JSON-file repository.

Writes atomically: serialise to a sibling ``.tmp`` file, fsync, then rename
over the target. On a crash mid-write, the previous version stays intact.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class JsonFileRepository:
    """Persist arbitrary JSON-serialisable values under ``data/<key>.json``.

    The ``key`` may contain forward slashes (e.g. ``"social/alice"``);
    sub-directories are created on demand.
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, value: Any) -> None:
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(value, fh, indent=2, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)

    def load(self, key: str) -> Any | None:
        path = self._path_for(key)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def list_keys(self, prefix: str) -> list[str]:
        base = (self._root / prefix).parent if "/" in prefix else self._root
        if not base.exists():
            return []
        keys: list[str] = []
        for p in base.rglob("*.json"):
            rel = p.relative_to(self._root)
            key = str(rel.with_suffix(""))
            if key.startswith(prefix):
                keys.append(key)
        return sorted(keys)

    def _path_for(self, key: str) -> Path:
        return self._root / f"{key}.json"
