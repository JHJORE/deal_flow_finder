from dataclasses import dataclass, field

from deal_flow.domain.entities.founder import Founder


@dataclass(frozen=True)
class PortfolioCompany:
    name: str
    detail_url: str
    website: str | None = None
    sector: str | None = None
    description: str | None = None
    linkedin_url: str | None = None
    founders: tuple[Founder, ...] = field(default_factory=tuple)
