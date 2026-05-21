"""SEC filings port."""

from __future__ import annotations

from typing import Protocol

from pipeline.entities.models import Filing
from pipeline.entities.value_objects import Timestamp


class FilingFetcher(Protocol):
    def search_form_d(self, investor_alias: str, since: Timestamp) -> list[Filing]:
        """Return Form D filings where ``investor_alias`` is a named investor."""
        ...
