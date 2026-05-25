from dataclasses import dataclass, field
from datetime import date

from deal_flow.domain.value_objects.form_d_related_person import FormDRelatedPerson


@dataclass(frozen=True)
class FormDFiling:
    accession_number: str
    issuer_name: str
    issuer_cik: str
    filed_at: date
    url: str
    total_offering_amount: int | None = None
    total_amount_sold: int | None = None
    related_persons: tuple[FormDRelatedPerson, ...] = field(default_factory=tuple)
    is_pooled_investment_fund: bool = False
    industry_group: str | None = None
