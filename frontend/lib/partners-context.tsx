"use client";

import { useEffect, useState } from "react";

import { fetchPartnerProfiles } from "./api/partners";
import { FIRM_META, _setPartners, buildPartnersFromProfiles } from "./data";
import type { FirmId } from "./types";

export function PartnersProvider({ children }: { children: React.ReactNode }) {
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const firms: FirmId[] = ["sequoia", "a16z", "yc"];
        const results = await Promise.all(
          firms.map(async (firm) => {
            const profiles = await fetchPartnerProfiles(FIRM_META[firm].domain);
            return buildPartnersFromProfiles(profiles, firm);
          })
        );
        if (cancelled) return;
        _setPartners(results.flat());
      } catch (err) {
        console.warn("partner-profiles fetch failed; rendering empty list", err);
        if (cancelled) return;
        _setPartners([]);
      }
      setLoaded(true);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // Don't render children until partners are loaded — every view reads
  // PARTNERS from `lib/data` synchronously, and we don't want to invasively
  // subscribe each one to a hook just to trigger a re-render. A brief
  // loading flash on the first paint is the trade-off.
  if (!loaded) {
    return (
      <div className="flex min-h-screen items-center justify-center font-mono text-meta text-ink-4">
        loading partners…
      </div>
    );
  }

  return <>{children}</>;
}
