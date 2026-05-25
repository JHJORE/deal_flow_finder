"use client";

import { Avatar } from "@/components/Avatar";
import { StarToggle } from "@/components/DetailUI";
import { INK_ON_DARK, INK_ON_LIGHT, FOUNDER_AVATAR } from "@/lib/ui";
import { PageHeader } from "@/components/PageHeader";
import {
  COMPANIES,
  FILINGS,
  FIRMS,
  FOUNDERS,
  PARTNERS,
  SIGNALS,
  firmColor,
} from "@/lib/data";
import { useRadar } from "@/lib/state";

type PerfDirection = "up" | "down" | "flat";
type Perf = { direction: PerfDirection; magnitude: number; delta: number };

// Momentum = avg(last 3) − avg(first 3). Captures the arc of the series
// rather than the last single sample, which would be noisier.
function momentumFromSeries(series: number[] | undefined): Perf {
  if (!series || series.length < 4) return { direction: "flat", magnitude: 0, delta: 0 };
  const n = series.length;
  const recent = series.slice(n - 3).reduce((a, b) => a + b, 0) / 3;
  const earlier = series.slice(0, 3).reduce((a, b) => a + b, 0) / 3;
  const delta = recent - earlier;
  const base = Math.max(Math.abs(earlier), Math.abs(recent), 1);
  const magnitude = Math.min(1, Math.abs(delta) / base);
  const threshold = Math.max(1.5, base * 0.05);
  const direction: PerfDirection =
    delta > threshold ? "up" : delta < -threshold ? "down" : "flat";
  return { direction, magnitude, delta };
}

function PerformanceArrow({ perf }: { perf: Perf }) {
  const { direction, magnitude } = perf;
  // map magnitude → vertical reach. Flat indicators never travel even a hair —
  // the visual rest state is dead horizontal.
  const reach = direction === "flat" ? 0 : Math.max(0.25, magnitude) * 5.4;
  const cy = 8;
  const startX = 3.5;
  const endX = 26.5;
  const dy = direction === "up" ? -reach : direction === "down" ? reach : 0;
  const tipY = cy + dy;

  // Chevron arms angled 28° off the line's bearing, pointing back along it.
  const lineAngle = Math.atan2(dy, endX - startX);
  const armLen = 4.4;
  const fanRad = (28 * Math.PI) / 180;
  const a1 = lineAngle + Math.PI - fanRad;
  const a2 = lineAngle + Math.PI + fanRad;
  const arm1X = endX + Math.cos(a1) * armLen;
  const arm1Y = tipY + Math.sin(a1) * armLen;
  const arm2X = endX + Math.cos(a2) * armLen;
  const arm2Y = tipY + Math.sin(a2) * armLen;

  const strokeVar =
    direction === "up"
      ? "var(--accent)"
      : direction === "down"
      ? "var(--ink-3)"
      : "var(--ink-4)";

  return (
    <svg
      viewBox="0 0 30 16"
      width={30}
      height={16}
      className={`perf-arrow perf-${direction}`}
      aria-hidden="true"
    >
      <line
        x1={startX}
        x2={endX + 1}
        y1={cy}
        y2={cy}
        stroke="var(--line-faint)"
        strokeWidth={0.6}
        strokeDasharray="1.5 2.5"
      />
      <path
        d={`M ${startX} ${cy} L ${endX} ${tipY.toFixed(2)}`}
        stroke={strokeVar}
        strokeWidth={1.6}
        strokeLinecap="round"
        fill="none"
        className="perf-arrow-shaft"
      />
      <path
        d={`M ${endX} ${tipY.toFixed(2)} L ${arm1X.toFixed(2)} ${arm1Y.toFixed(
          2
        )} M ${endX} ${tipY.toFixed(2)} L ${arm2X.toFixed(2)} ${arm2Y.toFixed(2)}`}
        stroke={strokeVar}
        strokeWidth={1.6}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
        className="perf-arrow-head"
      />
    </svg>
  );
}

function PerformanceIndicator({ perf }: { perf: Perf }) {
  const { direction, delta } = perf;
  const rounded = Math.round(delta);
  const label =
    direction === "flat"
      ? "—"
      : `${rounded > 0 ? "+" : rounded < 0 ? "−" : ""}${Math.abs(rounded)}`;
  const colorClass =
    direction === "up"
      ? "text-accent"
      : direction === "down"
      ? "text-ink-3"
      : "text-ink-4";

  return (
    <span className="ml-auto flex items-center gap-2 perf-indicator">
      <PerformanceArrow perf={perf} />
      <span className={`font-mono text-meta tabnum ${colorClass}`} style={{ minWidth: "2.4ch", textAlign: "right" }}>
        {label}
      </span>
    </span>
  );
}

export function WatchlistView() {
  const { watchlist, archived, setOpen } = useRadar();

  if (watchlist.size === 0) {
    return (
      <>
        <PageHeader
          eyebrow="Watchlist"
          title={<>Your private radar.</>}
          description="Partners, founders and companies you are tracking. Signals involving anyone here are pinned to the top of your feed and flagged."
          showFirmFilter={false}
        />
        <div className="mx-auto max-w-[460px] rounded-lg border border-line-faint bg-surface-1 px-8 py-16 text-center">
          <div className="font-display text-[2.5rem] leading-none text-line-hard">☆</div>
          <h2 className="mt-4 t-h-md">Your watchlist is empty</h2>
          <p className="mt-3 t-caption !max-w-[40ch] mx-auto">
            Open any partner, founder or company and hit the <span className="text-accent">Watch</span> button.
            They will show up here, and their signals get pinned to the top of your feed.
          </p>
        </div>
      </>
    );
  }

  const watchedPartners = PARTNERS.filter((p) => watchlist.has(p.id));
  const watchedFounders = FOUNDERS.filter((f) => watchlist.has(f.id));
  const watchedCompanies = COMPANIES.filter((c) => watchlist.has(c.id));

  const liveSignals = SIGNALS.filter((s) => {
    if (archived.has(s.id)) return false;
    if (s.actors.some((a) => watchlist.has(a))) return true;
    if (s.filing && FILINGS[s.filing] && watchlist.has(FILINGS[s.filing].relatedCompany ?? "")) return true;
    return false;
  }).length;

  return (
    <>
      <PageHeader
        eyebrow="Watchlist"
        title={<>Your private radar.</>}
        description="Partners, founders and companies you are tracking. Signals involving anyone here are pinned to the top of your feed and flagged."
        showFirmFilter={false}
      />

      <Tracker
        tracked={watchlist.size}
        live={liveSignals}
        partners={watchedPartners.length}
        founders={watchedFounders.length}
        companies={watchedCompanies.length}
      />


      <Section title="Partners" count={watchedPartners.length}>
        {watchedPartners.map((p, i) => (
          <Card
            key={p.id}
            id={p.id}
            name={p.name}
            color={firmColor(p.firm)}
            sub={`${FIRMS[p.firm].name} · ${p.role}`}
            onOpen={() => setOpen({ kind: "partner", id: p.id })}
            perf={momentumFromSeries(p.engageRate)}
            index={i}
          />
        ))}
      </Section>

      <Section title="Founders" count={watchedFounders.length}>
        {watchedFounders.map((f, i) => (
          <Card
            key={f.id}
            id={f.id}
            name={f.name}
            color={FOUNDER_AVATAR}
            sub={f.role}
            onOpen={() => setOpen({ kind: "partner", id: f.id })}
            textDark
            perf={momentumFromSeries(f.engageRate)}
            index={i}
          />
        ))}
      </Section>

      <Section title="Portfolio companies" count={watchedCompanies.length}>
        {watchedCompanies.map((c, i) => (
          <Card
            key={c.id}
            id={c.id}
            name={c.name}
            color={firmColor(c.firm)}
            sub={`${FIRMS[c.firm].name}${c.sector ? ` · ${c.sector}` : ""} · ${c.stage}`}
            onOpen={() => setOpen({ kind: "company", id: c.id })}
            perf={momentumFromSeries(c.jobs)}
            index={i}
          />
        ))}
      </Section>
    </>
  );
}

function Tracker({
  tracked,
  live,
  partners,
  founders,
  companies,
}: {
  tracked: number;
  live: number;
  partners: number;
  founders: number;
  companies: number;
}) {
  const maxCat = Math.max(partners, founders, companies, 1);
  const dominant =
    partners >= founders && partners >= companies
      ? "partners"
      : founders >= companies
      ? "founders"
      : "companies";

  return (
    <div className="mb-7 overflow-hidden rounded-lg border border-line-faint bg-surface-1">
      <div className="flex items-center justify-between gap-4 border-b border-line-faint px-5 py-3 sm:px-6">
        <div className="flex items-baseline gap-3 stagger-in stagger-1">
          <span className="t-mono-cap">Your private radar</span>
          <span className="hidden h-1 w-1 rounded-full bg-line-hard sm:inline-block" />
          <span className="font-mono text-meta tabnum text-ink-3 hidden sm:inline">
            {tracked} tracked
          </span>
        </div>
        <div
          className="flex items-center gap-2 stagger-in stagger-2"
          aria-label={`${live} live signals on your list`}
        >
          {live > 0 && (
            <span
              className="radar-dot"
              style={{ background: "var(--accent)", boxShadow: "0 0 0 0 var(--accent-soft)" }}
            />
          )}
          <span
            className="font-mono tabnum text-meta font-semibold"
            style={{ color: live > 0 ? "var(--accent)" : "var(--ink-3)", letterSpacing: "0.08em" }}
          >
            {live} LIVE
          </span>
        </div>
      </div>

      <div className="grid grid-cols-3">
        <StatCell
          label="Partners"
          count={partners}
          share={partners / maxCat}
          accent={dominant === "partners"}
          delayMs={280}
        />
        <StatCell
          label="Founders"
          count={founders}
          share={founders / maxCat}
          accent={dominant === "founders"}
          delayMs={360}
          divider
        />
        <StatCell
          label="Companies"
          count={companies}
          share={companies / maxCat}
          accent={dominant === "companies"}
          delayMs={440}
          divider
        />
      </div>
    </div>
  );
}

function StatCell({
  label,
  count,
  share,
  accent,
  delayMs,
  divider = false,
}: {
  label: string;
  count: number;
  share: number;
  accent: boolean;
  delayMs: number;
  divider?: boolean;
}) {
  return (
    <div
      className={`stagger-in flex flex-col gap-4 px-5 py-6 sm:px-7 sm:py-7 ${
        divider ? "border-l border-line-faint" : ""
      }`}
      style={{ animationDelay: `${delayMs}ms` }}
    >
      <div className="flex items-baseline gap-3">
        <span
          className="font-display tabnum leading-none text-ink"
          style={{
            fontSize: "clamp(2.5rem, 6vw, 3.5rem)",
            fontWeight: 700,
            letterSpacing: "-0.035em",
            fontVariantNumeric: "tabular-nums lining-nums",
          }}
        >
          {count}
        </span>
        {count === 0 && (
          <span className="font-mono text-meta text-ink-4 lowercase">none yet</span>
        )}
      </div>
      <div className="h-[2px] w-full overflow-hidden bg-line-faint">
        <div
          className="score-bar-fill h-full"
          style={{
            width: `${Math.max(share * 100, count > 0 ? 6 : 0)}%`,
            background: accent ? "var(--accent)" : "var(--ink-3)",
          }}
        />
      </div>
      <span
        className="font-mono text-meta uppercase"
        style={{
          letterSpacing: "0.16em",
          color: accent ? "var(--accent)" : "var(--ink-3)",
          fontSize: "0.6875rem",
        }}
      >
        {label}
      </span>
    </div>
  );
}

function Section({ title, count, children }: { title: string; count: number; children: React.ReactNode }) {
  if (count === 0) return null;
  return (
    <section className="mb-7">
      <div className="mb-3 flex items-center gap-3">
        <h3 className="eyebrow !text-ink-3">{title}</h3>
        <span className="font-mono text-meta tabnum text-ink-4">{count}</span>
      </div>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">{children}</div>
    </section>
  );
}

function Card({
  id,
  name,
  color,
  sub,
  onOpen,
  textDark = false,
  perf,
  index = 0,
}: {
  id: string;
  name: string;
  color: string;
  sub: string;
  onOpen: () => void;
  textDark?: boolean;
  perf: Perf;
  index?: number;
}) {
  const titleLabel =
    perf.direction === "up"
      ? "Rising momentum"
      : perf.direction === "down"
      ? "Cooling momentum"
      : "Flat momentum";
  return (
    <article
      role="button"
      tabIndex={0}
      onClick={onOpen}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onOpen();
        }
      }}
      title={`${titleLabel} (${perf.delta >= 0 ? "+" : "−"}${Math.abs(Math.round(perf.delta))})`}
      className="group card-lift flex cursor-pointer items-center gap-3 rounded-md border border-line-faint bg-surface-1 px-4 py-3 text-left hover:border-line-hard focus:outline-none focus-visible:border-line-hard focus-visible:ring-2 focus-visible:ring-accent/40"
      style={{ ["--perf-stagger" as string]: `${index * 60}ms` }}
    >
      <Avatar
        name={name}
        color={color}
        size="sm"
        textColor={textDark ? INK_ON_LIGHT : INK_ON_DARK}
      />
      <div className="min-w-0 flex-1">
        <div className="truncate t-h-sm">{name}</div>
        <div className="truncate font-mono text-meta text-ink-4">{sub}</div>
      </div>
      <PerformanceIndicator perf={perf} />
      <StarToggle id={id} label={name} />
    </article>
  );
}
