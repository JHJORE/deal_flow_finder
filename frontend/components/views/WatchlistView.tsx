"use client";

import { Avatar } from "@/components/Avatar";
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

      <div className="mb-7 grid grid-cols-1 gap-px overflow-hidden rounded-lg border border-line-faint bg-line-faint sm:grid-cols-3">
        <Summary value={watchlist.size} label="tracked" />
        <Summary value={liveSignals} label="live signals on your list" tone="warn" />
        <Summary
          value={`${watchedPartners.length}/${watchedFounders.length}/${watchedCompanies.length}`}
          label="partners / founders / companies"
        />
      </div>

      <Section title="Partners" count={watchedPartners.length}>
        {watchedPartners.map((p) => (
          <Card
            key={p.id}
            name={p.name}
            color={firmColor(p.firm)}
            sub={`${FIRMS[p.firm].name} · ${p.role}`}
            onOpen={() => setOpen({ kind: "partner", id: p.id })}
          />
        ))}
      </Section>

      <Section title="Founders" count={watchedFounders.length}>
        {watchedFounders.map((f) => (
          <Card
            key={f.id}
            name={f.name}
            color={FOUNDER_AVATAR}
            sub={f.role}
            onOpen={() => setOpen({ kind: "partner", id: f.id })}
            textDark
          />
        ))}
      </Section>

      <Section title="Portfolio companies" count={watchedCompanies.length}>
        {watchedCompanies.map((c) => (
          <Card
            key={c.id}
            name={c.name}
            color={firmColor(c.firm)}
            sub={`${FIRMS[c.firm].name} · ${c.stage}`}
            onOpen={() => setOpen({ kind: "company", id: c.id })}
          />
        ))}
      </Section>
    </>
  );
}

function Summary({ value, label, tone = "default" }: { value: React.ReactNode; label: string; tone?: "default" | "warn" }) {
  return (
    <div className="flex flex-col gap-2 bg-surface-1 px-6 py-5">
      <span className={`n-md ${tone === "warn" ? "text-accent" : "text-ink"}`}>{value}</span>
      <span className="eyebrow">{label}</span>
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
  name,
  color,
  sub,
  onOpen,
  textDark = false,
}: {
  name: string;
  color: string;
  sub: string;
  onOpen: () => void;
  textDark?: boolean;
}) {
  return (
    <button
      onClick={onOpen}
      className="group card-lift flex items-center gap-3 rounded-md border border-line-faint bg-surface-1 px-4 py-3 text-left hover:border-line-hard"
    >
      <Avatar
        name={name}
        color={color}
        size="sm"
        textColor={textDark ? INK_ON_LIGHT : INK_ON_DARK}
      />
      <div className="min-w-0">
        <div className="truncate t-h-sm">{name}</div>
        <div className="truncate font-mono text-meta text-ink-4">{sub}</div>
      </div>
      <span className="ml-auto text-accent">★</span>
    </button>
  );
}
