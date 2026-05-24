"use client";

import {
  FILINGS,
  FIRMS,
  PARTNERS,
  THEMES,
  delta,
  founderById,
} from "@/lib/data";
import { useRadar } from "@/lib/state";
import type { Signal } from "@/lib/types";

type Props = { signals: Signal[] };

export function Briefing({ signals }: Props) {
  const { briefingDismissed, dismissBriefing, isWatched, activeFirms } = useRadar();
  if (briefingDismissed || signals.length === 0) return null;

  const lines = computeBriefing(signals, isWatched, activeFirms);
  if (lines.length === 0) return null;

  return (
    <section className="mb-7 rounded-lg border border-line-faint bg-surface-raised px-7 py-6">
      <div className="mb-4 flex items-baseline gap-4">
        <span className="eyebrow-accent">AI briefing</span>
        <span className="font-mono text-meta tabnum text-ink-4">
          synthesised from {signals.length} signals
        </span>
        <button
          onClick={dismissBriefing}
          className="ml-auto text-h-md leading-none text-ink-4 transition-colors hover:text-ink"
          aria-label="Dismiss briefing"
        >
          ×
        </button>
      </div>
      <ul className="space-y-3.5">
        {lines.map((l, i) => (
          <li key={i} className="flex gap-4">
            <span
              aria-hidden
              className="mt-[0.6rem] inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-accent"
            />
            <span
              className="t-body !max-w-none"
              dangerouslySetInnerHTML={{
                __html: l.replace(
                  /<strong>(.+?)<\/strong>/g,
                  '<span style="color:var(--accent);font-weight:600;">$1</span>'
                ),
              }}
            />
          </li>
        ))}
      </ul>
    </section>
  );
}

function computeBriefing(
  sigs: Signal[],
  isWatched: (id: string) => boolean,
  activeFirms: Set<string>
): string[] {
  const lines: string[] = [];

  for (const s of sigs.filter((x) => x.sources.includes("EDGAR"))) {
    const fil = s.filing ? FILINGS[s.filing] : undefined;
    if (!fil) continue;
    const formLabel = fil.formType.split(" — ")[0];
    const firmNames = s.firms.map((f) => FIRMS[f].name).join(" & ");
    const founder = s.actors.map((a) => founderById(a)).find(Boolean);
    const founderClause = founder ? `; issuer profile matches ${founder.name}` : "";
    lines.push(
      `EDGAR <strong>${formLabel}</strong> · ${firmNames} named in <strong>${fil.issuer}</strong>, not on the public portfolio${founderClause}.`
    );
  }

  const convs = sigs.filter((s) => s.headline.toLowerCase().startsWith("convergence"));
  if (convs.length > 0) {
    const names = convs
      .map((s) => {
        const f = s.actors.map((a) => founderById(a)).find(Boolean);
        return f ? f.name : null;
      })
      .filter(Boolean) as string[];
    lines.push(
      `<strong>${convs.length} partner-on-founder convergence event${
        convs.length === 1 ? "" : "s"
      }</strong> open${names.length ? ` — ${names.join(", ")}` : ""}.`
    );
  }

  const movers = THEMES.map((t) => {
    const d = delta(t.share);
    return { label: t.label, last: d[d.length - 1] };
  })
    .filter((m) => m.last !== 0)
    .sort((a, b) => Math.abs(b.last) - Math.abs(a.last))
    .slice(0, 3);
  if (movers.length > 0) {
    const top = movers
      .map((m) => `${m.label} ${m.last > 0 ? "+" : ""}${m.last}pts`)
      .join(", ");
    lines.push(`Theme drift this period — <strong>${top}</strong>.`);
  }

  const newTopicPartners = PARTNERS.filter(
    (p) => p.newTopic && activeFirms.has(p.firm)
  );
  if (newTopicPartners.length > 0) {
    const sample = newTopicPartners.slice(0, 3).map((p) => p.name).join(", ");
    const extra =
      newTopicPartners.length > 3 ? ` +${newTopicPartners.length - 3} more` : "";
    lines.push(
      `<strong>${newTopicPartners.length} partner${
        newTopicPartners.length === 1 ? "" : "s"
      }</strong> opened a new topic this period — ${sample}${extra}.`
    );
  }

  const watched = sigs.filter((s) => {
    const onActor = s.actors.some((a) => isWatched(a));
    const onCompany =
      s.filing &&
      FILINGS[s.filing] &&
      isWatched(FILINGS[s.filing].relatedCompany ?? "");
    return onActor || onCompany;
  });
  if (watched.length > 0) {
    lines.push(
      `<strong>${watched.length} signal${
        watched.length === 1 ? "" : "s"
      }</strong> touch your watchlist.`
    );
  }

  return lines;
}
