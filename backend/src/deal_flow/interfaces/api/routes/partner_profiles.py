from fastapi import APIRouter, Depends

from deal_flow.application.use_cases.load_firm_partner_profiles import (
    LoadFirmPartnerProfiles,
    LoadFirmPartnerProfilesInput,
)
from deal_flow.domain.entities.partner import Partner
from deal_flow.interfaces.api.dependencies import get_load_firm_partner_profiles

router = APIRouter(prefix="/api/firms", tags=["partner-profiles"])


@router.get("/{firm_domain}/partner-profiles")
def list_partner_profiles(
    firm_domain: str,
    use_case: LoadFirmPartnerProfiles = Depends(get_load_firm_partner_profiles),
) -> list[Partner]:
    return use_case.execute(LoadFirmPartnerProfilesInput(firm_domain=firm_domain))
