from dataclasses import dataclass

from deal_flow.domain.entities.form_d_filing import FormDFiling
from deal_flow.domain.value_objects.date_range import DateRange


@dataclass(frozen=True)
class PartnerFormDSignal:
    partner_name: str
    date_range: DateRange
    filings: tuple[FormDFiling, ...]
