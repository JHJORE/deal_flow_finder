"use client";

import { Avatar } from "@/components/Avatar";
import { StarToggle } from "@/components/DetailUI";
import { INK_ON_DARK } from "@/lib/ui";
import { PageHeader } from "@/components/PageHeader";
import { COMPANIES, FIRMS, firmColor } from "@/lib/data";
import { useRadar } from "@/lib/state";
import type { Company } from "@/lib/types";

function hiringLift(c: Company): number | null {
  const base = (c.jobs[0] + c.jobs[1] + c.jobs[2]) / 3;
  if (!base) return null;
  return Math.round(((c.jobs[c.jobs.length - 1] - base) / base) * 100);
}

function careersUrl(c: Company): string | null {
  if (!c.website) return null;
  return `${c.website.replace(/\/+$/, "")}/careers`;
}

export function PortfolioView() {
  const { activeFirms, setOpen, isWatched } = useRadar();
  const cs = COMPANIES.filter((c) => activeFirms.has(c.firm)).sort(
    (a, b) => a.name.localeCompare(b.name)
  );

  return (
    <>
      <PageHeader eyebrow="Portfolio · hiring signals" />

      {cs.length === 0 ? (
        <Empty />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cs.map((c) => (
            <CompanyCard
              key={c.id}
              company={c}
              watched={isWatched(c.id)}
              onOpen={() => setOpen({ kind: "company", id: c.id })}
            />
          ))}
        </div>
      )}
    </>
  );
}

function CompanyCard({ company, onOpen, watched }: { company: Company; onOpen: () => void; watched: boolean }) {
  const lift = hiringLift(company);
  const hotHires = company.seniorHires.filter((h) => h.hot).length;
  const sectorOrStage = company.sector || company.stage;
  const careers = careersUrl(company);

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
      className="group card-lift flex cursor-pointer flex-col gap-3 rounded-lg border border-line-faint bg-surface-1 px-5 py-5 text-left hover:border-line-hard focus:outline-none focus-visible:border-line-hard focus-visible:ring-2 focus-visible:ring-accent/40"
    >
      <div className="flex items-center gap-3">
        <Avatar
          name={company.name}
          color={firmColor(company.firm)}
          size="md"
          textColor={INK_ON_DARK}
          watched={watched}
          photoUrl={company.photoUrl}
        />
        <div className="min-w-0 flex-1">
          <div className="truncate t-h-sm">{company.name}</div>
          <div className="t-meta truncate">
            {FIRMS[company.firm].name}
            {sectorOrStage ? ` · ${sectorOrStage}` : ""}
          </div>
        </div>
        <StarToggle id={company.id} label={company.name} />
      </div>

      <p className="t-caption !max-w-none line-clamp-2 min-h-[3em] text-ink-2">
        {company.description ?? `${company.sector || "Portfolio"} company · founded by ${company.founder || "—"}`}
      </p>

      <div className="flex items-center justify-between gap-3">
        {hotHires > 0 ? (
          <div className="font-mono text-meta tabnum text-accent">
            + {hotHires} fundraise-signal hire{hotHires > 1 ? "s" : ""}
          </div>
        ) : (
          <div className="font-mono text-meta text-ink-4">— steady on hires</div>
        )}
        {careers && (
          <a
            href={careers}
            target="_blank"
            rel="noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="font-mono text-meta text-ink-3 underline-offset-2 hover:text-ink hover:underline"
          >
            careers ↗
          </a>
        )}
      </div>

      <div className="mt-1 grid grid-cols-3 gap-4 border-t border-line-faint pt-4">
        <Stat label="open roles" value={company.jobs[company.jobs.length - 1] ?? "—"} />
        <Stat
          label="hiring vs base"
          value={lift === null ? "—" : `${lift > 0 ? "+" : ""}${lift}%`}
          tone={lift !== null && lift > 40 ? "warn" : "default"}
        />
        <Stat
          label="senior hires"
          value={company.seniorHires.length}
          tone={hotHires > 0 ? "warn" : "default"}
        />
      </div>
    </article>
  );
}

function Stat({ label, value, tone = "default" }: { label: string; value: React.ReactNode; tone?: "default" | "warn" }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className={`n-sm ${tone === "warn" ? "text-accent" : "text-ink"}`}>{value}</span>
      <span className="eyebrow">{label}</span>
    </div>
  );
}

function Empty() {
  return (
    <div className="rounded-lg border border-line-faint bg-surface-1 px-6 py-12 text-center text-caption text-ink-3">
      No portfolio companies in this filter.
    </div>
  );
}
