"use client";

import { useEffect } from "react";
import { Sidebar } from "./Sidebar";
import { useRadar } from "@/lib/state";
import { SignalsView } from "./views/SignalsView";
import { PeopleView } from "./views/PeopleView";
import { PortfolioView } from "./views/PortfolioView";
import { ConsensusView } from "./views/ConsensusView";
import { GraphsView } from "./views/GraphsView";
import { WatchlistView } from "./views/WatchlistView";
import { PartnerProfileView } from "./views/PartnerProfileView";
import { CompanyProfileView } from "./views/CompanyProfileView";
import { FilingView } from "./views/FilingView";
import type { ViewId } from "@/lib/types";

const KEY_TO_VIEW: Record<string, ViewId> = {
  "1": "signals",
  "2": "people",
  "3": "portfolio",
  "4": "consensus",
  "5": "graph",
  w: "watchlist",
  W: "watchlist",
};

export function AppShell() {
  const { view, open, setView, setOpen } = useRadar();

  // power-user keyboard shortcuts
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable)) {
        return;
      }
      if (e.metaKey || e.ctrlKey || e.altKey) return;

      if (e.key === "Escape" && open) {
        e.preventDefault();
        setOpen(null);
        return;
      }
      const next = KEY_TO_VIEW[e.key];
      if (next) {
        e.preventDefault();
        setView(next);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, setOpen, setView]);

  // discreet console greeting for the curious
  useEffect(() => {
    if (typeof window === "undefined") return;
    // eslint-disable-next-line no-console
    console.log(
      "%cDealflow Radar%c · pre-deal signal intelligence\n%cKeyboard: 1–5 switch views · W watchlist · Esc closes drilldown",
      "font-family: 'Bricolage Grotesque', serif; font-size: 14px; font-weight: 700; color: oklch(72% 0.155 50); letter-spacing: -0.02em;",
      "font-family: 'Hanken Grotesk', sans-serif; font-size: 12px; color: oklch(70% 0.010 65);",
      "font-family: 'Fragment Mono', monospace; font-size: 11px; color: oklch(56% 0.010 65); letter-spacing: 0.02em;"
    );
  }, []);

  return (
    <div className="grid min-h-screen grid-cols-[244px_1fr] bg-surface-0">
      <Sidebar />
      <main className="max-w-[1240px] px-10 py-8 pb-24">
        {open ? <Drilldown /> : <RootView view={view} />}
      </main>
    </div>
  );
}

function RootView({ view }: { view: string }) {
  switch (view) {
    case "signals":
      return <SignalsView />;
    case "people":
      return <PeopleView />;
    case "portfolio":
      return <PortfolioView />;
    case "consensus":
      return <ConsensusView />;
    case "graph":
      return <GraphsView />;
    case "watchlist":
      return <WatchlistView />;
    default:
      return <SignalsView />;
  }
}

function Drilldown() {
  const { open } = useRadar();
  if (!open) return null;
  if (open.kind === "partner") return <PartnerProfileView id={open.id} />;
  if (open.kind === "company") return <CompanyProfileView id={open.id} />;
  if (open.kind === "filing") return <FilingView id={open.id} />;
  return null;
}
