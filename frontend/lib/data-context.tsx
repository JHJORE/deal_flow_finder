"use client";

import { useEffect, useState } from "react";

import { fetchPartnerProfiles } from "./api/partners";
import { fetchPortfolioCompanies } from "./api/portfolio";
import {
  FIRM_META,
  _setCompanies,
  _setPartners,
  buildCompaniesFromPortfolio,
  buildPartnersFromProfiles,
} from "./data";
import type { FirmId } from "./types";

const FIRMS: FirmId[] = ["sequoia", "a16z", "yc"];

export function DataProvider({ children }: { children: React.ReactNode }) {
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        // Six fetches in one parallel wave: 3 firms × {partners, portfolio}.
        // Both endpoints are pure JSON reads on the backend so latency is
        // dominated by the slowest single round-trip.
        const partnersPerFirm = FIRMS.map((firm) =>
          fetchPartnerProfiles(FIRM_META[firm].domain)
        );
        const portfolioPerFirm = FIRMS.map((firm) =>
          fetchPortfolioCompanies(FIRM_META[firm].domain)
        );
        const [partnerResults, portfolioResults] = await Promise.all([
          Promise.all(partnersPerFirm),
          Promise.all(portfolioPerFirm),
        ]);
        if (cancelled) return;
        const partners = partnerResults.flatMap((profiles, i) =>
          buildPartnersFromProfiles(profiles, FIRMS[i])
        );
        _setPartners(partners);
        // Portfolio build runs after _setPartners so the dev-mode partner-slug
        // sanity check in buildCompaniesFromPortfolio sees the populated list.
        const companies = portfolioResults.flatMap((profiles, i) =>
          buildCompaniesFromPortfolio(profiles, FIRMS[i])
        );
        _setCompanies(companies);
      } catch (err) {
        console.warn(
          "data fetch failed; rendering empty partners/portfolio",
          err
        );
        if (cancelled) return;
        _setPartners([]);
        _setCompanies([]);
      }
      setLoaded(true);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // Same loading-gate trade-off as PartnersProvider: views read PARTNERS /
  // COMPANIES synchronously, so we hold the first paint until both arrays
  // are populated rather than threading a hook through every consumer.
  if (!loaded) {
    return (
      <div className="flex min-h-screen items-center justify-center font-mono text-meta text-ink-4">
        loading…
      </div>
    );
  }

  return <>{children}</>;
}
