from dataclasses import dataclass, replace

from deal_flow.application.ports.repositories.partner_profile_repository import (
    PartnerProfileRepository,
)
from deal_flow.application.use_cases.summarize_partner_bio import (
    SummarizePartnerBio,
    SummarizePartnerBioInput,
)
from deal_flow.domain.entities.partner import Partner


@dataclass(frozen=True)
class LoadFirmPartnerProfilesInput:
    firm_domain: str
    summarize: bool = True


class LoadFirmPartnerProfiles:
    """Read persisted partner profiles for a firm; optionally run each
    non-empty bio through the bio-summarizer so the UI gets a short
    ``about_short`` instead of the full multi-paragraph bio.

    The summarizer's own on-disk cache makes repeat calls free, so we don't
    layer a second cache here.
    """

    def __init__(
        self,
        repo: PartnerProfileRepository,
        summarize_bio: SummarizePartnerBio,
    ) -> None:
        self._repo = repo
        self._summarize_bio = summarize_bio

    def execute(self, input: LoadFirmPartnerProfilesInput) -> list[Partner]:
        partners = self._repo.list_by_firm(input.firm_domain)
        if not input.summarize:
            return partners
        return [self._with_summary(p) for p in partners]

    def _with_summary(self, partner: Partner) -> Partner:
        if partner.about_short or not partner.bio:
            return partner
        summary = self._summarize_bio.execute(SummarizePartnerBioInput(bio=partner.bio))
        return replace(partner, about_short=summary.about_short)
