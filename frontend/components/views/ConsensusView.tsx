"use client";

import { Avatar } from "@/components/Avatar";
import { INK_ON_DARK, INK_ON_LIGHT, FOUNDER_AVATAR } from "@/lib/ui";
import { DriftChart } from "@/components/DriftChart";
import { PageHeader } from "@/components/PageHeader";
import {
  COMPANIES,
  COMPANY_TOPICS,
  FIRMS,
  FOUNDERS,
  PARTNERS,
  THEMES,
  delta,
  firmColor,
  themeByKey,
  themeColor,
} from "@/lib/data";
import { useRadar } from "@/lib/state";
import type { ThemeKey } from "@/lib/types";
import { useMemo } from "react";

function activeThemeUsage(activeFirms: Set<string>) {
  const map: Record<string, { partners: string[]; founders: string[]; companies: string[] }> = {};
  THEMES.forEach((t) => (map[t.key] = { partners: [], founders: [], companies: [] }));
  PARTNERS.filter((p) => activeFirms.has(p.firm)).forEach((p) => {
    p.engages.forEach((k) => {
      if (map[k]) map[k].partners.push(p.id);
    });
  });
  FOUNDERS.forEach((f) => {
    f.engages.forEach((k) => {
      if (map[k]) map[k].founders.push(f.id);
    });
  });
  COMPANIES.filter((c) => activeFirms.has(c.firm)).forEach((c) => {
    const topics = COMPANY_TOPICS[c.id] || [];
    const keys = Array.from(new Set(topics.map((t) => t.themeKey).filter(Boolean)));
    keys.forEach((k) => {
      if (map[k as string]) map[k as string].companies.push(c.id);
    });
  });
  return map;
}

export function ConsensusView() {
  const { activeFirms, selectedTheme, setSelectedTheme } = useRadar();
  const usage = useMemo(() => activeThemeUsage(activeFirms), [activeFirms]);

  const ranked = useMemo(
    () =>
      [...THEMES].sort((a, b) => {
        const da = delta(a.share);
        const db = delta(b.share);
        return db[db.length - 1] - da[da.length - 1];
      }),
    []
  );

  const theme = themeByKey(selectedTheme as ThemeKey) ?? ranked[0];
  const lastChg = delta(theme.share)[theme.share.length - 1];

  return (
    <>
      <PageHeader
        eyebrow="Consensus tracker"
        title={<>Where attention is concentrating.</>}
        description="Aggregated theme attention across the ecosystem. Click a theme to see exactly which partners, tracked founders and portfolio companies are engaging it."
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.5fr_1fr]">
        <section className="panel px-6 py-6">
          <div className="mb-4 flex items-baseline justify-between">
            <h2 className="t-h-sm">Theme drift</h2>
            <span className="font-mono text-meta tabnum text-ink-4">mention share · 6 months</span>
          </div>
          <Legend />
          <DriftChart />
        </section>

        <section className="panel px-6 py-6">
          <h2 className="mb-4 t-h-sm">Ranked by movement</h2>
          <ul className="flex flex-col gap-1">
            {ranked.map((t) => {
              const d = delta(t.share);
              const last = d[d.length - 1];
              const up = last >= 0;
              const isSelected = t.key === selectedTheme;
              return (
                <li key={t.key}>
                  <button
                    onClick={() => setSelectedTheme(t.key)}
                    className={`relative flex w-full items-center gap-3 rounded-md px-3 py-3 text-left transition-colors ${
                      isSelected ? "bg-surface-2" : "hover:bg-surface-2/60"
                    }`}
                  >
                    <span
                      className="h-2 w-2 shrink-0 rounded-full"
                      style={{ background: themeColor(t) }}
                    />
                    <span className="grow">
                      <span className="block t-h-sm text-ink">{t.label}</span>
                      <span className="font-mono text-meta tabnum text-ink-4">{t.age}</span>
                    </span>
                    <span className="text-right">
                      <span className={`block n-sm ${up ? "text-positive" : "text-negative"}`}>
                        {up ? "+" : ""}
                        {last} pts
                      </span>
                      <span className="font-mono text-eyebrow tabnum text-ink-4">vs prior</span>
                    </span>
                    {isSelected && <span className="absolute right-2 top-2 h-1 w-1 rounded-full bg-accent" />}
                  </button>
                </li>
              );
            })}
          </ul>
        </section>
      </div>

      <section className="panel mt-6 px-7 py-7">
        <div className="mb-5 flex items-start justify-between gap-4 border-b border-line-faint pb-5">
          <div>
            <div
              className="font-mono text-eyebrow uppercase tracking-[0.18em]"
              style={{ color: themeColor(theme) }}
            >
              Inspecting theme
            </div>
            <h2 className="mt-1 t-h-lg">{theme.label}</h2>
            <div className="font-mono text-meta tabnum text-ink-4 mt-1">{theme.age}</div>
          </div>
          <div className="text-right">
            <div className={`n-lg ${lastChg >= 0 ? "text-positive" : "text-negative"}`}>
              {lastChg >= 0 ? "+" : ""}
              {lastChg} pts
            </div>
            <div className="font-mono text-meta tabnum text-ink-4 mt-1">vs prior period</div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-7 md:grid-cols-3">
          <Column
            count={usage[theme.key].partners.length}
            prefix="partners engaging"
            themeName={theme.label}
            themeAccent={themeColor(theme)}
            entries={usage[theme.key].partners}
            type="partner"
            empty="No partners in current firm filter."
          />
          <Column
            count={usage[theme.key].founders.length}
            prefix="tracked founders building"
            themeName={theme.label}
            themeAccent={themeColor(theme)}
            entries={usage[theme.key].founders}
            type="founder"
            empty="No tracked founders yet."
          />
          <Column
            count={usage[theme.key].companies.length}
            prefix="portfolio companies on"
            themeName={theme.label}
            themeAccent={themeColor(theme)}
            entries={usage[theme.key].companies}
            type="company"
            empty="No portfolio companies on this theme."
          />
        </div>
      </section>
    </>
  );
}

function Legend() {
  const { setSelectedTheme } = useRadar();
  return (
    <div className="mb-4 flex flex-wrap gap-x-4 gap-y-2">
      {THEMES.map((t) => (
        <button
          key={t.key}
          onClick={() => setSelectedTheme(t.key)}
          className="inline-flex items-center gap-2 text-meta text-ink-2 transition-colors hover:text-ink"
        >
          <span className="h-1 w-3 rounded-sm" style={{ background: themeColor(t) }} />
          {t.label}
        </button>
      ))}
    </div>
  );
}

function Column({
  count,
  prefix,
  themeName,
  themeAccent,
  entries,
  type,
  empty,
}: {
  count: number;
  prefix: string;
  themeName: string;
  themeAccent: string;
  entries: string[];
  type: "partner" | "founder" | "company";
  empty: string;
}) {
  const { setOpen, isWatched } = useRadar();

  return (
    <div>
      <div className="mb-4 flex items-baseline gap-2">
        <span className="n-sm text-ink">{count}</span>
        <span className="eyebrow">
          {prefix}{" "}
          <span style={{ color: themeAccent }}>{themeName}</span>
        </span>
      </div>
      <div className="flex flex-col gap-1.5">
        {entries.length === 0 ? (
          <div className="font-mono text-meta text-ink-4">{empty}</div>
        ) : (
          entries.map((id) => {
            if (type === "company") {
              const c = COMPANIES.find((x) => x.id === id)!;
              return (
                <button
                  key={id}
                  onClick={() => setOpen({ kind: "company", id })}
                  className="flex items-center gap-3 rounded-md border border-line-faint bg-surface-2/40 px-3 py-2 text-left transition-colors hover:border-line-hard hover:bg-surface-2"
                >
                  <Avatar
                    name={c.name}
                    color={firmColor(c.firm)}
                    size="sm"
                    textColor={INK_ON_DARK}
                    watched={isWatched(id)}
                  />
                  <span className="flex flex-col">
                    <span className="t-h-sm">{c.name}</span>
                    <span className="font-mono text-meta text-ink-4">{FIRMS[c.firm].name} portfolio</span>
                  </span>
                </button>
              );
            }
            const isPartner = type === "partner";
            const partner = isPartner ? PARTNERS.find((p) => p.id === id) : undefined;
            const founder = !isPartner ? FOUNDERS.find((f) => f.id === id) : undefined;
            const e = (partner ?? founder)!;
            const col = partner ? firmColor(partner.firm) : FOUNDER_AVATAR;
            const textColor = partner ? INK_ON_DARK : INK_ON_LIGHT;
            const sub = partner ? FIRMS[partner.firm].name : "founder";
            return (
              <button
                key={id}
                onClick={() => setOpen({ kind: "partner", id })}
                className="flex items-center gap-3 rounded-md border border-line-faint bg-surface-2/40 px-3 py-2 text-left transition-colors hover:border-line-hard hover:bg-surface-2"
              >
                <Avatar
                  name={e.name}
                  color={col}
                  size="sm"
                  textColor={textColor}
                  watched={isWatched(id)}
                />
                <span className="flex flex-col">
                  <span className="t-h-sm">{e.name}</span>
                  <span className="font-mono text-meta text-ink-4">{sub}</span>
                </span>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
