import hashlib
import json
from pathlib import Path
from typing import Any


class FileCache:
    """SHA256-keyed JSON file cache for external-API responses."""

    def __init__(self, cache_dir: Path) -> None:
        self._dir = cache_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key_for(method: str, **kwargs: Any) -> str:
        payload = json.dumps(
            {"method": method, **kwargs}, sort_keys=True, default=str
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:32]

    def path_for(self, key: str) -> Path:
        return self._dir / f"{key}.json"

    def read(self, key: str) -> dict[str, Any] | None:
        path = self.path_for(key)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def write(self, key: str, payload: dict[str, Any]) -> Path:
        path = self.path_for(key)
        path.write_text(json.dumps(payload, default=str, indent=2), encoding="utf-8")
        return path
