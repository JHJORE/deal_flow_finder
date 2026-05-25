from abc import ABC, abstractmethod

from deal_flow.domain.entities.partner import Partner


class PartnerProfileRepository(ABC):
    """Read access to persisted partner profile data (the scraped JSON sitting
    in ``backend/data/``). Distinct from the live-scrape path used by
    ``ExtractFirmPartners`` — this repo serves the snapshot, fast and offline.
    """

    @abstractmethod
    def list_by_firm(self, firm_domain: str) -> list[Partner]:
        """Return all known partners for ``firm_domain`` (e.g. ``"a16z.com"``).
        Empty list if the firm has no persisted data."""
