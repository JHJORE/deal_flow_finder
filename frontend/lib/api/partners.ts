// Shape returned by GET /api/firms/{domain}/partner-profiles.
// Mirrors backend domain entity Partner (deal_flow.domain.entities.partner).
export type PartnerProfileDTO = {
  name: string;
  profile_url: string;
  role: string | null;
  role_display: string | null;
  focus_areas: string[];
  teams: string[];
  bio: string | null;
  about_short: string | null;
  linkedin_url: string | null;
  x_url: string | null;
  email: string | null;
  photo_url: string | null;
  education: string[];
  prior_experience: string[];
};

export async function fetchPartnerProfiles(
  firmDomain: string,
  opts: { summarize?: boolean } = {}
): Promise<PartnerProfileDTO[]> {
  const summarize = opts.summarize ?? true;
  const res = await fetch(
    `/api/firms/${encodeURIComponent(firmDomain)}/partner-profiles?summarize=${summarize}`,
    { cache: "no-store" }
  );
  if (!res.ok) {
    throw new Error(`partner-profiles ${firmDomain} → HTTP ${res.status}`);
  }
  return res.json();
}
