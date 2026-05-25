from abc import ABC, abstractmethod

from deal_flow.domain.entities.partner import Partner


class PartnerDirectory(ABC):
    """Read-only directory of a firm's partners.

    Returns the partner roster as it was last captured — the source of
    truth for partner identity, LinkedIn URLs, etc. Live re-scraping is a
    separate concern handled by ``ExtractFirmPartners``.
    """

    @abstractmethod
    def list_partners(self, firm_domain: str) -> list[Partner]:
        """Return all partners for ``firm_domain``.

        Raises ``FileNotFoundError`` (or domain equivalent) if no directory
        entry exists for the firm.
        """
