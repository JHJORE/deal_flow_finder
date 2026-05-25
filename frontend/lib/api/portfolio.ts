// Shape returned by GET /api/firms/{domain}/portfolio-profiles.
// Mirrors backend domain entity PortfolioCompany
// (deal_flow.domain.entities.portfolio_company).
export type PortfolioFounderDTO = {
  name: string;
  role: string | null;
};

export type PortfolioCompanyDTO = {
  name: string;
  detail_url: string;
  website: string | null;
  sector: string | null;
  description: string | null;
  linkedin_url: string | null;
  photo_url: string | null;
  founders: PortfolioFounderDTO[];
};

export async function fetchPortfolioCompanies(
  firmDomain: string
): Promise<PortfolioCompanyDTO[]> {
  const res = await fetch(
    `/api/firms/${encodeURIComponent(firmDomain)}/portfolio-profiles`,
    { cache: "no-store" }
  );
  if (!res.ok) {
    throw new Error(`portfolio-profiles ${firmDomain} → HTTP ${res.status}`);
  }
  return res.json();
}
