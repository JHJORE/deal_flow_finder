from dataclasses import dataclass

from deal_flow.application.ports.repositories.partner_profile_repository import (
    PartnerProfileRepository,
)
from deal_flow.domain.entities.partner import Partner


@dataclass(frozen=True)
class LoadFirmPartnerProfilesInput:
    firm_domain: str


class LoadFirmPartnerProfiles:
    """Read persisted partner profiles for a firm.

    ``about_short`` is expected to be filled in by the scrape pipeline and
    persisted into the JSON file — not computed on the request path. The
    request path stays cheap and free of external LLM dependencies.
    """

    def __init__(self, repo: PartnerProfileRepository) -> None:
        self._repo = repo

    def execute(self, input: LoadFirmPartnerProfilesInput) -> list[Partner]:
        return self._repo.list_by_firm(input.firm_domain)
