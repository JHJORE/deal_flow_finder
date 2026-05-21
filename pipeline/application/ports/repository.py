"""Generic persistence port.

Implementations live in ``adapters/storage/``. Use cases never know whether
the backing store is JSON files, SQLite, or a real database — only that they
can save/load by a string key.
"""

from __future__ import annotations

from typing import Any, Protocol


class EntityRepository(Protocol):
    """Generic key/value persistence over JSON-serialisable values."""

    def save(self, key: str, value: Any) -> None:
        """Persist ``value`` under ``key``. Implementations must be atomic."""
        ...

    def load(self, key: str) -> Any | None:
        """Return the value at ``key`` or ``None`` if absent."""
        ...

    def list_keys(self, prefix: str) -> list[str]:
        """Return all keys starting with ``prefix``, sorted."""
        ...
