from abc import ABC, abstractmethod

from deal_flow.domain.entities.partner_form_d_signal import PartnerFormDSignal


class BoardSeatLog(ABC):
    """Durable store of filtered Form D board-seat signals."""

    @abstractmethod
    def append(self, signal: PartnerFormDSignal) -> None:
        """Persist new filings from `signal`, deduped by (partner, accession)."""
