from abc import ABC, abstractmethod
from datetime import date


class SecFilingSearcher(ABC):
    @abstractmethod
    def search_form_d(self, query: str, start: date, end: date) -> list[dict]:
        """Return Form D hits matching ``query`` in the inclusive window.
        Each dict has: accession_number, issuer_name, issuer_cik, filed_at
        (ISO string), url.
        """

    @abstractmethod
    def fetch_primary_doc(self, accession_number: str, cik: str) -> dict:
        """Fetch and parse the filing's ``primary_doc.xml``.

        Returns a dict with keys:
        - ``issuer_name``: str
        - ``related_persons``: list of {first_name, last_name, relationships
          (list[str]), relationship_clarification (str | None)}
        - ``industry_group``: str | None
        - ``is_pooled_investment_fund``: bool
        """
