"use client";

import {
  FILINGS,
  FIRMS,
  actorById,
  confAccent,
  firmColor,
  founderById,
  partnerById,
  tierAccent,
  tierName,
} from "@/lib/data";
import { INK_ON_LIGHT } from "@/lib/ui";
import { useRadar } from "@/lib/state";
import type { Signal } from "@/lib/types";
import { Avatar } from "./Avatar";

type Props = { signal: Signal; compact?: boolean };

export function SignalCard({ signal, compact = false }: Props) {
  const { setOpen, archiveSignal, isWatched } = useRadar();
  const hasFiling = !!(signal.filing && FILINGS[signal.filing]);
  const onWatch = isOnWatch(signal, isWatched);
  const rec = signalRecommendation(signal);

  function go() {
    if (hasFiling) {
      setOpen({ kind: "filing", id: signal.filing! });
      return;
    }
    const firstFounder = signal.actors.find((a) => founderById(a));
    const firstPartner = signal.actors.find((a) => partnerById(a));
    const target = firstFounder ?? firstPartner;
    if (target) {
      const kind = partnerById(target) ? "partner" : "company";
      if (founderById(target)) setOpen({ kind: "partner", id: target });
      else setOpen({ kind, id: target });
    }
  }

  // Tier 1 signals are the product's headline value (convergence, undisclosed
  // Form D). They earn a visible step up in scale + spacing so the feed has
  // genuine hierarchy instead of reading flat.
  const isHero = signal.tier === 1 && !compact;

  return (
    <article
      onClick={go}
      className={`group card-lift cursor-pointer rounded-lg border border-line-faint bg-surface-1 hover:border-line-hard ${
        isHero ? "px-7 py-6" : "px-6 py-5"
      }`}
    >
      <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-2">
        {onWatch && (
          <span className="inline-flex items-center gap-1 rounded-sm bg-accent/15 px-2 py-0.5 text-eyebrow font-bold uppercase text-accent">
            ★ Watching
          </span>
        )}
        <span
          className={`inline-flex items-center rounded-sm font-bold uppercase text-eyebrow ${
            isHero ? "px-2.5 py-1 tracking-[0.12em]" : "px-2 py-0.5"
          }`}
          style={{
            color: tierAccent[signal.tier],
            background: `color-mix(in oklch, ${tierAccent[signal.tier]} ${isHero ? 18 : 14}%, transparent)`,
          }}
        >
          {tierName[signal.tier]}
        </span>
        <span
          className="inline-flex items-center gap-1.5 text-meta"
          style={{ color: confAccent[signal.conf] }}
        >
          <span
            className="h-1 w-1 rounded-full"
            style={{ background: confAccent[signal.conf] }}
          />
          {signal.conf === "med" ? "medium" : signal.conf} confidence
        </span>
        <div className="flex flex-wrap gap-1">
          {signal.sources.map((src) => (
            <span
              key={src}
              className="rounded-sm border border-line-faint px-1.5 py-0.5 font-mono text-eyebrow tracking-[0.04em] text-ink-3"
            >
              {src}
            </span>
          ))}
        </div>
        <span className="ml-auto font-mono text-meta tabnum text-ink-4">
          {signal.age} · score {signal.score}
        </span>
        {!compact && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              archiveSignal(signal.id);
            }}
            className="rounded-sm border border-line-faint px-2 py-0.5 text-eyebrow font-bold uppercase text-ink-4 transition-colors hover:border-line-hard hover:text-ink"
          >
            archive
          </button>
        )}
      </div>

      <h3 className={isHero ? "t-h-lg" : "t-h-md text-ink"}>{signal.headline}</h3>
      <p className={`t-body text-ink-2 ${isHero ? "mt-3" : "mt-2"}`}>{signal.body}</p>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {signal.actors.map((aid, i) => {
          const a = actorById(aid);
          if (!a) return null;
          const isP = !!partnerById(aid);
          const col = isP ? firmColor((a as any).firm) : "var(--ink)";
          return (
            <span key={aid} className="flex items-center gap-2">
              <span className="inline-flex items-center gap-2 rounded-full border border-line-faint bg-surface-2 py-1 pl-1 pr-3">
                <Avatar
                  name={a.name}
                  color={col}
                  size="xs"
                  textColor={isP ? "oklch(96% 0 0)" : INK_ON_LIGHT}
                />
                <span className="text-meta font-medium text-ink">{a.name}</span>
              </span>
              {i < signal.actors.length - 1 && (
                <span className="text-ink-4" aria-hidden>
                  +
                </span>
              )}
            </span>
          );
        })}
      </div>

      {hasFiling && (
        <div className="mt-3 inline-flex items-center gap-1.5 font-mono text-meta text-accent">
          Open Form D filing →
        </div>
      )}

      <div
        className="mt-4 rounded-md px-4 py-3"
        style={{
          background:
            rec.status === "actionable"
              ? "color-mix(in oklch, var(--positive) 7%, var(--surface-2))"
              : "color-mix(in oklch, var(--negative) 7%, var(--surface-2))",
        }}
      >
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <span
            className="font-mono text-eyebrow font-bold uppercase"
            style={{ color: rec.status === "actionable" ? "var(--positive)" : "var(--negative)" }}
          >
            {rec.label}
          </span>
          <span className="t-caption text-ink-2">{rec.action}</span>
        </div>
      </div>

      <div className="mt-4 h-px w-full overflow-hidden bg-line-faint">
        <div
          className="score-bar-fill h-full"
          style={{
            width: `${signal.score}%`,
            background:
              signal.score >= 85
                ? "var(--positive)"
                : signal.score >= 65
                ? "var(--accent)"
                : "var(--ink-3)",
            opacity: 0.85,
          }}
        />
      </div>
    </article>
  );
}

function isOnWatch(s: Signal, isWatched: (id: string) => boolean) {
  if (s.actors.some((a) => isWatched(a))) return true;
  if (s.filing && FILINGS[s.filing] && isWatched(FILINGS[s.filing].relatedCompany ?? "")) {
    return true;
  }
  return false;
}

export type SignalRecommendation = {
  status: "actionable" | "closed";
  label: string;
  action: string;
};

export function signalRecommendation(s: Signal): SignalRecommendation {
  const hasFiling = s.filing && FILINGS[s.filing];
  if (hasFiling) {
    const fil = FILINGS[s.filing!];
    const founderName = fil.relatedFounder
      ? founderById(fil.relatedFounder)?.name ?? "the founder"
      : "the founder";
    return {
      status: "closed",
      label: "Deal closed — too late for this round",
      action: `This round is already done; you cannot invest in it. Use it as a lead: the theme is now validated by a real check, and ${fil.namedInvestor} is actively writing here. Source the earlier-stage companies in this space, and watch ${founderName}'s network for who builds next.`,
    };
  }
  if (s.headline.toLowerCase().includes("convergence")) {
    const f = s.actors.map((a) => founderById(a)).find(Boolean);
    return {
      status: "actionable",
      label: "Open — act now",
      action: `Two partners are circling ${
        f ? f.name : "this founder"
      } but no deal has closed. This is the window. Reach out before a term sheet appears.`,
    };
  }
  if (s.tier === 1) {
    return {
      status: "actionable",
      label: "Open — act now",
      action: "A check is forming but not yet written. Move now, while the round is still open.",
    };
  }
  if (s.tier === 2) {
    return {
      status: "actionable",
      label: "Open — get ahead of it",
      action: "This founder is preparing to raise. Build the relationship before the round opens.",
    };
  }
  if (s.tier === 3) {
    return {
      status: "actionable",
      label: "Open — early",
      action:
        "A company here barely exists yet. Get in front of the founder before anyone else notices.",
    };
  }
  return {
    status: "actionable",
    label: "Watch — thesis level",
    action: "No single deal to chase. Use this to steer where you source: scan this theme for early founders.",
  };
}

export { isOnWatch };
