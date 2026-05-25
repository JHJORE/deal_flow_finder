"use client";

import { Briefing } from "@/components/Briefing";
import { KPI, KPIGrid } from "@/components/KPI";
import { PageHeader } from "@/components/PageHeader";
import { SignalCard } from "@/components/SignalCard";
import { FILINGS, PARTNERS, SIGNALS, tierName } from "@/lib/data";
import { useRadar } from "@/lib/state";
import type { Signal } from "@/lib/types";
import { useEffect, useMemo, useState } from "react";

const TIER_FILTERS: { value: "all" | "1" | "2" | "3" | "4"; label: string }[] = [
  { value: "all", label: "All signals" },
  { value: "1", label: tierName[1] },
  { value: "2", label: tierName[2] },
  { value: "3", label: tierName[3] },
  { value: "4", label: tierName[4] },
];

export function SignalsView() {
  const { activeFirms, feedFilter, setFeedFilter, archived, isWatched, watchlist, unarchiveAll } =
    useRadar();

  const visible = useMemo(() => {
    return SIGNALS.filter((s) => {
      if (archived.has(s.id)) return false;
      const firmOk = s.firms.length === 0 || s.firms.some((f) => activeFirms.has(f));
      const tierOk = feedFilter === "all" || String(s.tier) === feedFilter;
      return firmOk && tierOk;
    }).sort((a, b) => {
      const wa = signalTouchesWatch(a, isWatched) ? 1 : 0;
      const wb = signalTouchesWatch(b, isWatched) ? 1 : 0;
      if (wa !== wb) return wb - wa;
      const ea = a.sources.includes("EDGAR") ? 1 : 0;
      const eb = b.sources.includes("EDGAR") ? 1 : 0;
      if (ea !== eb) return eb - ea;
      return b.score - a.score;
    });
  }, [activeFirms, feedFilter, archived, isWatched, watchlist]);

  const conv = visible.filter((s) => s.headline.toLowerCase().includes("convergence")).length;
  const edgar = visible.filter((s) => s.sources.includes("EDGAR")).length;
  const spiking = PARTNERS.filter((p) => activeFirms.has(p.firm) && p.spike).length;

  const dateline = useLiveDateline();

  return (
    <>
      <PageHeader
        eyebrow="Signal feed · live"
        title={<>What partners and portfolio companies are doing right now.</>}
        description="Cross-source observations from X, LinkedIn and SEC EDGAR, ranked by tier."
        dateline={dateline}
      />

      <KPIGrid>
        <KPI label="Live signals" value={visible.length} hint="in current filter" />
        <KPI label="Partner convergence" value={conv} hint="2+ partners, one founder" tone="warn" />
        <KPI label="Partners spiking" value={spiking} hint="engagement above baseline" tone="up" />
        <KPI label="EDGAR confirmations" value={edgar} hint="undisclosed Form D" tone="warn" />
      </KPIGrid>

      <ScanLine />

      <Briefing signals={visible} />

      <div className="mb-5 flex flex-wrap items-center gap-2">
        {TIER_FILTERS.map((f) => {
          const active = feedFilter === f.value;
          return (
            <button
              key={f.value}
              onClick={() => setFeedFilter(f.value)}
              className={`rounded-full border px-3.5 py-1 text-meta font-medium transition-colors ${
                active
                  ? "border-accent bg-accent text-surface-0"
                  : "border-line-faint text-ink-3 hover:border-line-hard hover:text-ink"
              }`}
            >
              {f.label}
            </button>
          );
        })}
      </div>

      <div className="flex flex-col gap-3">
        {visible.length === 0 ? (
          <div className="rounded-lg border border-line-faint bg-surface-1 px-6 py-12 text-center text-caption text-ink-3">
            No signals here.{" "}
            {archived.size > 0 && (
              <button onClick={unarchiveAll} className="ml-1 font-semibold text-accent underline-offset-2 hover:underline">
                Restore {archived.size} archived
              </button>
            )}
          </div>
        ) : (
          visible.map((s) => <SignalCard key={s.id} signal={s} />)
        )}
      </div>
    </>
  );
}

function useLiveDateline() {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => {
    setNow(new Date());
    const id = setInterval(() => setNow(new Date()), 60_000);
    return () => clearInterval(id);
  }, []);
  return useMemo(() => {
    if (!now) return undefined;
    const formatted = now.toLocaleDateString("en-GB", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
    return `Daily digest · ${formatted}`;
  }, [now]);
}

function ScanLine() {
  return (
    <div className="my-5 flex items-center gap-3 font-mono text-meta tabnum text-ink-4">
      <span className="radar-dot" />
      <span>Live scan · {SIGNALS.length} signals tracked · refreshed 23 hours ago</span>
    </div>
  );
}

function signalTouchesWatch(s: Signal, isWatched: (id: string) => boolean) {
  if (s.actors.some((a) => isWatched(a))) return true;
  if (s.filing && FILINGS[s.filing] && isWatched(FILINGS[s.filing].relatedCompany ?? "")) {
    return true;
  }
  return false;
}
