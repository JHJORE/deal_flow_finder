"use client";

import { THEMES, themeByKey, themeColor } from "@/lib/data";
import { useRadar } from "@/lib/state";
import type { Theme, ThemeKey, TopicRow, ViewId } from "@/lib/types";

// match a free-text topic label against the tracked theme palette so partner /
// founder topic bars adopt the same color as the consensus drift chart
function inferTheme(label: string): Theme | null {
  const norm = label.toLowerCase();
  return (
    THEMES.find((t) => norm === t.label.toLowerCase()) ??
    THEMES.find((t) => norm.startsWith(t.label.toLowerCase())) ??
    null
  );
}

export function BackButton({ to }: { to?: ViewId }) {
  const { setView, view } = useRadar();
  return (
    <button
      onClick={() => setView(to ?? view)}
      className="mb-7 inline-flex items-center gap-2 font-mono text-meta tabnum text-ink-3 transition-colors hover:text-accent"
    >
      <span aria-hidden>←</span>
      <span>back to {(to ?? view).replace(/^./, (c) => c.toUpperCase())}</span>
    </button>
  );
}

export function ProfileHeader({
  avatar,
  name,
  role,
  rightSlot,
  handle,
}: {
  avatar: React.ReactNode;
  name: string;
  role: string;
  handle?: string;
  rightSlot?: React.ReactNode;
}) {
  return (
    <header className="mb-7 flex items-start gap-5">
      {avatar}
      <div className="grow">
        <h1 className="t-h-xl text-ink">{name}</h1>
        <div className="mt-2 t-caption text-ink-2 !max-w-none">{role}</div>
        {handle && <div className="mt-1 font-mono text-meta text-ink-4">{handle}</div>}
      </div>
      {rightSlot && <div className="shrink-0">{rightSlot}</div>}
    </header>
  );
}

export function WatchButton({ id }: { id: string }) {
  const { isWatched, toggleWatch } = useRadar();
  const on = isWatched(id);
  return (
    <button
      onClick={() => toggleWatch(id)}
      className={`inline-flex items-center gap-2 rounded-md border px-4 py-2 text-meta font-semibold transition-colors ${
        on
          ? "border-accent bg-accent text-surface-0"
          : "border-line text-ink-2 hover:border-line-hard hover:text-ink"
      }`}
    >
      {/* key forces a remount so the scale animation replays on every toggle */}
      <span key={on ? "on" : "off"} aria-hidden className="watch-pop">
        {on ? "★" : "☆"}
      </span>
      <span>{on ? "Watching" : "Watch"}</span>
    </button>
  );
}

export function StatRow({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-6 grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-line-faint bg-line-faint md:grid-cols-4">
      {children}
    </div>
  );
}

export function Stat({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: React.ReactNode;
  hint: string;
  tone?: "default" | "up" | "warn" | "down";
}) {
  const toneClass: Record<string, string> = {
    default: "text-ink",
    up: "text-positive",
    warn: "text-accent",
    down: "text-negative",
  };
  return (
    <div className="flex flex-col gap-2 bg-surface-1 px-5 py-5">
      <span className="eyebrow">{label}</span>
      <span className={`n-md ${toneClass[tone]}`}>{value}</span>
      <span className="font-mono text-meta tabnum text-ink-4">{hint}</span>
    </div>
  );
}

export function Panel({
  label,
  subLabel,
  pill,
  children,
  className = "",
}: {
  label: string;
  subLabel?: string;
  pill?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel px-6 py-6 ${className}`}>
      <div className="mb-4 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h3 className="eyebrow !text-ink-3">{label}</h3>
        {pill && (
          <span className="rounded-sm bg-accent/15 px-2 py-0.5 font-mono text-eyebrow font-bold uppercase text-accent">
            {pill}
          </span>
        )}
        {subLabel && <span className="font-mono text-meta tabnum text-ink-4">{subLabel}</span>}
      </div>
      {children}
    </section>
  );
}

export function TopicsList({ topics }: { topics: TopicRow[] }) {
  return (
    <ul className="flex flex-col gap-3">
      {topics.map((t, i) => {
        // tie bar color to the tracked theme palette when this topic maps to one
        const theme = t.themeKey ? themeByKey(t.themeKey as ThemeKey) : inferTheme(t.t);
        const themeHue = theme ? themeColor(theme) : null;
        const barColor = themeHue ?? (t.isNew ? "var(--accent)" : "var(--line-hard)");
        const newDotColor = themeHue ?? "var(--accent)";
        return (
          <li key={i} className="flex items-center gap-3 text-caption">
            <span className="flex min-w-[150px] items-center gap-2 font-medium text-ink">
              {t.t}
              {t.isNew && (
                <span
                  className="h-1.5 w-1.5 rounded-full"
                  style={{ background: newDotColor }}
                  aria-hidden
                />
              )}
            </span>
            <span className="relative h-[6px] grow overflow-hidden rounded-sm bg-surface-2">
              <span
                className="absolute inset-y-0 left-0 rounded-sm"
                style={{
                  width: `${t.w}%`,
                  background: barColor,
                  opacity: themeHue && !t.isNew ? 0.72 : 1,
                }}
              />
            </span>
            <span className="w-10 text-right font-mono text-meta tabnum text-ink-4">{t.w}%</span>
            <span
              className={`w-14 text-right font-mono text-meta tabnum ${
                t.chg > 3 ? "text-positive" : "text-ink-4"
              }`}
            >
              {t.chg > 0 ? "+" : ""}
              {t.chg} pts
            </span>
          </li>
        );
      })}
    </ul>
  );
}

export function Interp({ children }: { children: React.ReactNode }) {
  return (
    <section className="mb-6 rounded-lg bg-surface-raised px-6 py-5">
      <div className="mb-2 eyebrow-accent">Read</div>
      <p className="t-body text-ink !max-w-[70ch]">{children}</p>
    </section>
  );
}

export function Timeline({
  items,
}: {
  items: { date?: string; title: string; description: string; hot?: boolean; flag?: string }[];
}) {
  return (
    <ol className="relative ml-2 border-l border-line-faint pl-5">
      {items.map((it, i) => (
        <li key={i} className="relative mb-5 last:mb-0">
          <span
            className="absolute -left-[22px] top-1 inline-block h-3 w-3 rounded-full"
            style={{
              background: it.hot ? "var(--accent)" : "var(--ink-4)",
              boxShadow: "0 0 0 3px var(--surface-1)",
            }}
            aria-hidden
          />
          {it.date && (
            <div className="mb-1 flex items-center gap-2 font-mono text-meta tabnum text-ink-4">
              {it.flag && (
                <span className="rounded-sm bg-positive px-1.5 py-0.5 text-eyebrow font-bold uppercase text-surface-0">
                  {it.flag}
                </span>
              )}
              {it.date}
            </div>
          )}
          <div className="t-h-sm">{it.title}</div>
          <div className="t-caption text-ink-3 !max-w-none">{it.description}</div>
        </li>
      ))}
    </ol>
  );
}

export function ContactRows({ rows }: { rows: { key: string; value: string; href?: string }[] }) {
  return (
    <div className="flex flex-col">
      {rows.map((r, i) => {
        const inner = (
          <>
            <span className="min-w-[70px] font-mono text-eyebrow uppercase text-ink-4">
              {r.key}
            </span>
            <span className="font-mono text-caption tabnum text-ink break-all">{r.value}</span>
          </>
        );
        const cls =
          "flex items-center gap-4 border-b border-line-faint px-2 py-3 last:border-b-0 transition-colors";
        if (r.href) {
          return (
            <a
              key={i}
              href={r.href}
              target={r.href.startsWith("http") ? "_blank" : undefined}
              rel="noopener"
              className={`${cls} hover:bg-surface-2/60`}
            >
              {inner}
            </a>
          );
        }
        return (
          <div key={i} className={cls}>
            {inner}
          </div>
        );
      })}
    </div>
  );
}
