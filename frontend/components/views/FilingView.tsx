"use client";

import { Avatar } from "@/components/Avatar";
import { INK_ON_DARK, INK_ON_LIGHT, FOUNDER_AVATAR } from "@/lib/ui";
import {
  BackButton,
  Interp,
  Panel,
  Timeline,
} from "@/components/DetailUI";
import {
  FILINGS,
  FIRMS,
  companyById,
  firmColor,
  founderById,
} from "@/lib/data";
import { useRadar } from "@/lib/state";
import type { FirmId } from "@/lib/types";

// resolve the firm id from a free-text "namedInvestor" string ("a16z" → "a16z")
function namedInvestorFirm(name: string): FirmId | null {
  const norm = name.toLowerCase();
  if (norm.includes("a16z") || norm.includes("andreessen")) return "a16z";
  if (norm.includes("sequoia")) return "sequoia";
  if (norm.includes("y combinator") || norm.includes("yc")) return "yc";
  return null;
}

export function FilingView({ id }: { id: string }) {
  const filing = FILINGS[id];
  if (!filing) return null;
  const { setOpen } = useRadar();

  const founder = filing.relatedFounder ? founderById(filing.relatedFounder) : null;
  const company = filing.relatedCompany ? companyById(filing.relatedCompany) : null;

  const facts: [string, string][] = [
    ["Form type", filing.formType],
    ["Filed", filing.filedDate],
    ["SEC CIK", filing.cik],
    ["Exemption claimed", filing.exemption],
    ["Total offering amount", filing.offeringAmount],
    ["Sold to date", filing.soldToDate],
    ["Investors in round", String(filing.totalInvestors)],
    ["Date of first sale", filing.firstSale],
    ["Industry (as filed)", filing.industry],
    ["Jurisdiction", filing.state],
  ];

  return (
    <div className="view-in">
      <BackButton to="signals" />

      <header className="mb-10 border-b border-line-faint pb-8">
        <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
          <span className="t-mono-cap !text-accent">SEC EDGAR · Form D · Undisclosed</span>
          <span className="t-mono-cap">Filing · {filing.cik}</span>
        </div>
        <h1 className="mt-6 font-display text-h-3xl font-bold text-ink max-w-[16ch]">
          {filing.issuer}
        </h1>
        <div className="mt-6 flex flex-wrap items-baseline gap-x-4 gap-y-2 t-lead !max-w-none">
          <span className="text-ink-3">Named investor</span>
          <NamedInvestor name={filing.namedInvestor} />
          <span className="font-mono text-meta tabnum text-ink-4">
            {filing.offeringAmount} raised across {filing.totalInvestors} investors
          </span>
        </div>
      </header>

      <Interp>{filing.whyFlagged}</Interp>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Panel label="Filing detail">
          <table className="w-full border-collapse">
            <tbody>
              {facts.map(([k, v]) => (
                <tr key={k} className="border-b border-line-faint last:border-b-0">
                  <td className="py-3 pr-3 eyebrow !text-ink-4 align-top whitespace-nowrap">
                    {k}
                  </td>
                  <td className="py-3 pl-3 text-right t-caption !max-w-none font-semibold tabnum text-ink">
                    {v}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mt-5 border-t border-line-faint pt-4">
            <div className="mb-2 eyebrow">Related persons on the filing</div>
            {filing.relatedPersons.map((p) => (
              <div key={p} className="py-1 text-meta text-ink-3">
                {p}
              </div>
            ))}
          </div>
        </Panel>

        <Panel label="Filing timeline">
          <Timeline
            items={filing.timeline.map((t) => ({
              date: t.d,
              title: t.t,
              description: t.s,
              hot: true,
            }))}
          />

          {founder && (
            <div className="mt-5 border-t border-line-faint pt-4">
              <div className="mb-2 eyebrow">Likely founder behind the issuer</div>
              <button
                onClick={() => setOpen({ kind: "partner", id: founder.id })}
                className="flex items-center gap-3 rounded-md border border-line-faint bg-surface-2/40 px-3 py-2 text-left transition-colors hover:border-line-hard"
              >
                <Avatar
                  name={founder.name}
                  color={FOUNDER_AVATAR}
                  size="sm"
                  textColor={INK_ON_LIGHT}
                />
                <span className="flex flex-col">
                  <span className="t-h-sm">{founder.name}</span>
                  <span className="font-mono text-meta text-ink-4">open founder dossier →</span>
                </span>
              </button>
            </div>
          )}

          {company && (
            <div className="mt-4">
              <div className="mb-2 eyebrow">Portfolio company entry</div>
              <button
                onClick={() => setOpen({ kind: "company", id: company.id })}
                className="flex items-center gap-3 rounded-md border border-line-faint bg-surface-2/40 px-3 py-2 text-left transition-colors hover:border-line-hard"
              >
                <Avatar
                  name={company.name}
                  color={firmColor(company.firm)}
                  size="sm"
                  textColor={INK_ON_DARK}
                />
                <span className="flex flex-col">
                  <span className="t-h-sm">{company.name}</span>
                  <span className="font-mono text-meta text-ink-4">
                    view hiring & company detail →
                  </span>
                </span>
              </button>
            </div>
          )}

          <a
            href={filing.edgarUrl}
            target="_blank"
            rel="noopener"
            className="mt-5 inline-block rounded-md border border-line px-4 py-2 font-mono text-meta tabnum text-info transition-colors hover:border-info hover:bg-surface-2"
          >
            Open on SEC EDGAR ↗
          </a>
        </Panel>
      </div>
    </div>
  );
}

function NamedInvestor({ name }: { name: string }) {
  const fid = namedInvestorFirm(name);
  const color = fid ? firmColor(fid) : "var(--ink)";
  const display = fid ? FIRMS[fid].name : name;
  return (
    <span
      className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-h-sm font-semibold"
      style={{
        background: `color-mix(in oklch, ${color} 16%, transparent)`,
        color: color,
      }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} aria-hidden />
      {display}
    </span>
  );
}
