from abc import ABC, abstractmethod
from datetime import date


class SecFilingSearcher(ABC):
    @abstractmethod
    def search_form_d(self, query: str, start: date, end: date) -> list[dict]:
        """Return Form D hits matching ``query`` in the inclusive window.
        Each dict has: accession_number, issuer_name, issuer_cik, filed_at
        (ISO string), url.
        """
