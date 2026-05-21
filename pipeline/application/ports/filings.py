"""SEC filings port."""

from __future__ import annotations

from typing import Protocol

from pipeline.entities.models import Filing
from pipeline.entities.value_objects import Timestamp


class FilingFetcher(Protocol):
    def search_form_d(
        self, first_name: str, last_name: str, since: Timestamp
    ) -> list[Filing]:
        """Return Form D filings naming this person as a Director / Related Person.

        Implementations tokenize the query as
        ``"first_name" AND "last_name" AND "Director"`` so a fund GP sitting
        on a stealth startup's board surfaces even when the fund entity
        itself is not named on the filing.
        """
        ...
