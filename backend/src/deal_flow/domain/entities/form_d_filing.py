from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class FormDFiling:
    accession_number: str
    issuer_name: str
    issuer_cik: str
    filed_at: date
    url: str
