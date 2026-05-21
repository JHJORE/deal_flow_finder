"""Configuration port.

Use cases need typed access to firm definitions, the operator watchlist, and
manual handle overrides. They must not know whether these come from YAML,
JSON, a database, or a remote config service. Adapters in
``pipeline/adapters/config/`` implement this protocol.
"""

from __future__ import annotations

from typing import Protocol

from pipeline.entities.models import Firm, WatchlistEntry


class ConfigRepository(Protocol):
    """Read-only access to the deployment's static configuration."""

    def load_firms(self) -> list[Firm]:
        """Return every firm the pipeline crawls."""
        ...

    def load_watchlist(self) -> list[WatchlistEntry]:
        """Return the operator watchlist used for stealth detection."""
        ...

    def load_handle_overrides(self) -> dict[str, str]:
        """Return manual ``name → x-handle`` overrides for ``DiscoverHandles``."""
        ...
