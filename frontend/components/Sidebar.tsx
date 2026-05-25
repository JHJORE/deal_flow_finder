"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { RadarMark } from "./RadarMark";
import { useRadar } from "@/lib/state";
import type { ViewId } from "@/lib/types";

const PRIMARY: { id: ViewId; label: string; index: string }[] = [
  { id: "signals", label: "Signal feed", index: "01" },
  { id: "people", label: "People watch", index: "02" },
  { id: "portfolio", label: "Portfolio", index: "03" },
  { id: "consensus", label: "Consensus", index: "04" },
  { id: "graph", label: "Graphs", index: "05" },
];

type IntegrationKey = "email" | "slack" | "mcp";

const INTEGRATIONS: {
  key: IntegrationKey;
  label: string;
  title: string;
  body: string;
}[] = [
  {
    key: "email",
    label: "Daily email digest",
    title: "Daily email digest",
    body:
      "Get a once-a-day email summarising new partner moves, hiring spikes, and theme drift. Reply to the email in plain language to tell Radar what you care about — it will weight future digests toward those firms, sectors, or signals.",
  },
  {
    key: "slack",
    label: "Slack alerts",
    title: "Slack alerts",
    body:
      "The same signals piped into a Slack channel of your choice, in near-real-time. Useful when a partner you watch starts posting about something new, or a portfolio company opens a CFO role.",
  },
  {
    key: "mcp",
    label: "MCP / agent access",
    title: "MCP / agent access",
    body:
      "Expose Radar as an MCP server so Claude, ChatGPT, or any agent client can query partners, portfolio hiring signals, and theme drift on your behalf — bring Radar's data into whatever workflow you already run.",
  },
];

export function Sidebar() {
  const { view, setView, watchlist, open } = useRadar();
  const currentTop = open ? null : view;
  const [openIntegration, setOpenIntegration] = useState<IntegrationKey | null>(null);
  const popoverRef = useRef<HTMLDivElement | null>(null);
  const triggersRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!openIntegration) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpenIntegration(null);
    }
    function onClick(e: MouseEvent) {
      const target = e.target as Node;
      if (popoverRef.current?.contains(target)) return;
      if (triggersRef.current?.contains(target)) return;
      setOpenIntegration(null);
    }
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onClick);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onClick);
    };
  }, [openIntegration]);

  const active = INTEGRATIONS.find((i) => i.key === openIntegration);

  return (
    <aside className="sticky top-0 flex h-screen w-[244px] shrink-0 flex-col gap-1 border-r border-line-faint bg-surface-0 px-5 py-7">
      <button
        type="button"
        onClick={() => setView("signals")}
        aria-label="Go to Signal feed"
        className="-mx-1 rounded-md px-1 py-1 text-left transition-colors hover:bg-surface-1"
      >
        <div className="flex items-center gap-3">
          <RadarMark size={22} className="text-accent shrink-0" />
          <div className="flex items-baseline gap-1.5 leading-[1]">
            <span className="font-display text-h-md font-bold text-ink">Dealflow</span>
            <span className="font-display text-h-md font-bold text-accent">Radar</span>
          </div>
        </div>
      </button>

      <a
        href="https://launch.co"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="by Launch"
        className="group mb-10 ml-[34px] inline-flex w-fit items-center gap-2 rounded-full border border-line-faint bg-[#000] px-3 py-[6px] transition-colors hover:border-line hover:bg-[#0a0a0a]"
      >
        <span className="eyebrow !text-ink-2 group-hover:!text-ink">by</span>
        <Image
          src="/launch.png"
          alt="Launch"
          width={418}
          height={121}
          priority
          className="h-[15px] w-auto"
        />
      </a>

      <div className="eyebrow mb-2 px-1">Views</div>
      <nav className="flex flex-col gap-[2px]">
        {PRIMARY.map((item) => {
          const isActive = currentTop === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setView(item.id)}
              className={`group relative flex items-center gap-3 rounded-md px-2.5 py-2 text-left transition-colors ${
                isActive ? "bg-surface-2 text-ink" : "text-ink-3 hover:bg-surface-1 hover:text-ink"
              }`}
            >
              <span
                className={`font-mono text-meta tabnum ${
                  isActive ? "text-accent" : "text-ink-4"
                }`}
              >
                {item.index}
              </span>
              <span className="text-caption font-medium text-current">{item.label}</span>
              {isActive && (
                <span
                  aria-hidden
                  className="absolute right-2.5 h-1.5 w-1.5 rounded-full bg-accent"
                />
              )}
            </button>
          );
        })}

        <WatchlistNavItem active={currentTop === "watchlist"} count={watchlist.size} />
      </nav>

      <div className="mt-auto" />

      <div className="eyebrow mb-2 mt-8 px-1">Integrations</div>
      <div ref={triggersRef} className="relative flex flex-col">
        {INTEGRATIONS.map((i) => (
          <IntegrationLine
            key={i.key}
            label={i.label}
            active={openIntegration === i.key}
            onClick={() =>
              setOpenIntegration((cur) => (cur === i.key ? null : i.key))
            }
          />
        ))}
        {active && (
          <div
            ref={popoverRef}
            role="dialog"
            aria-label={active.title}
            className="absolute left-full top-0 z-50 ml-3 w-[280px] rounded-lg border border-line bg-surface-1 px-4 py-4 shadow-xl"
          >
            <div className="mb-2 flex items-start justify-between gap-3">
              <div className="t-h-sm">{active.title}</div>
              <button
                onClick={() => setOpenIntegration(null)}
                aria-label="Close"
                className="-mt-0.5 -mr-1 rounded p-1 font-mono text-meta text-ink-4 transition-colors hover:bg-surface-2 hover:text-ink"
              >
                ×
              </button>
            </div>
            <p className="t-caption !max-w-none text-ink-2">{active.body}</p>
            <div className="mt-3 eyebrow">Coming soon</div>
          </div>
        )}
      </div>

      <div className="mt-7 border-t border-line-faint pt-4">
        <p className="px-1 text-meta text-ink-4">
          Sources: VC firm sites, X, LinkedIn, SEC EDGAR. Partner rosters are real;
          historic signal data is illustrative.
        </p>
      </div>
    </aside>
  );
}

function WatchlistNavItem({ active, count }: { active: boolean; count: number }) {
  const { setView } = useRadar();
  return (
    <button
      onClick={() => setView("watchlist")}
      className={`group relative mt-1 flex items-center gap-3 rounded-md px-2.5 py-2 text-left transition-colors ${
        active ? "bg-surface-2 text-ink" : "text-ink-3 hover:bg-surface-1 hover:text-ink"
      }`}
    >
      <span
        aria-hidden
        className={`font-mono text-meta tabnum ${active ? "text-accent" : "text-ink-4"}`}
      >
        ★
      </span>
      <span className="text-caption font-medium">Watchlist</span>
      {count > 0 && (
        <span className="ml-auto inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-accent px-1.5 text-eyebrow font-bold text-surface-0 tabnum tracking-normal">
          {count}
        </span>
      )}
      {active && (
        <span
          aria-hidden
          className="absolute right-2.5 h-1.5 w-1.5 rounded-full bg-accent"
        />
      )}
    </button>
  );
}

function IntegrationLine({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-expanded={active}
      className={`flex items-center justify-between rounded-md px-2.5 py-1.5 text-left text-caption transition-colors ${
        active
          ? "bg-surface-2 text-ink"
          : "text-ink-3 hover:bg-surface-1 hover:text-ink"
      }`}
    >
      <span>{label}</span>
      <span
        className={`font-mono text-eyebrow ${active ? "text-accent" : "text-ink-4"}`}
      >
        {active ? "open" : "soon"}
      </span>
    </button>
  );
}
