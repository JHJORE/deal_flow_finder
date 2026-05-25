"use client";

import { Avatar } from "@/components/Avatar";
import { INK_ON_DARK } from "@/lib/ui";
import {
  BackButton,
  ContactRows,
  Interp,
  Panel,
  ProfileHeader,
  Stat,
  StatRow,
  Timeline,
  TopicsList,
  WatchButton,
} from "@/components/DetailUI";
import { MiniBarChart } from "@/components/MiniChart";
import { SignalCard } from "@/components/SignalCard";
import {
  COMPANY_TOPICS,
  FILINGS,
  FIRMS,
  SIGNALS,
  companyById,
  firmColor,
  partnerById,
} from "@/lib/data";
import { useRadar } from "@/lib/state";

export function CompanyProfileView({ id }: { id: string }) {
  const company = companyById(id);
  if (!company) return null;

  const { setOpen } = useRadar();
  const base = (company.jobs[0] + company.jobs[1] + company.jobs[2]) / 3;
  const lift = base
    ? Math.round(((company.jobs[company.jobs.length - 1] - base) / base) * 100)
    : null;
  const dealPartner = company.deal.partner ? partnerById(company.deal.partner) : null;
  const coTopics = COMPANY_TOPICS[company.id] || [];

  // Only signals we can tie back: ones whose Form D filing names this company.
  const relatedSignals = SIGNALS.filter(
    (s) => s.filing && FILINGS[s.filing]?.relatedCompany === company.id
  );

  const founderHandle =
    company.foundersList.length === 0
      ? "founders not listed"
      : `founders: ${company.foundersList.map((f) => f.name).join(", ")}`;

  const contactRows = [
    company.contact.linkedin
      ? { key: "LinkedIn", value: company.contact.linkedin, href: `https://${company.contact.linkedin}` }
      : null,
    company.contact.site
      ? { key: "Website", value: company.contact.site, href: `https://${company.contact.site}` }
      : null,
    company.detailUrl
      ? {
          key: `${FIRMS[company.firm].name} portfolio`,
          value: company.detailUrl.replace(/^https?:\/\/(www\.)?/i, "").replace(/\/+$/, ""),
          href: company.detailUrl,
        }
      : null,
  ].filter((r): r is { key: string; value: string; href: string } => r !== null);

  return (
    <div className="view-in">
      <BackButton to="portfolio" />

      <ProfileHeader
        avatar={
          <Avatar
            name={company.name}
            color={firmColor(company.firm)}
            size="xl"
            textColor={INK_ON_DARK}
            photoUrl={company.photoUrl}
          />
        }
        name={company.name}
        role={`${company.sector || "Portfolio company"} · ${company.stage} · backed by ${FIRMS[company.firm].name}`}
        handle={founderHandle}
        rightSlot={<WatchButton id={company.id} />}
      />

      <StatRow>
        <Stat label="Open roles" value={company.jobs[company.jobs.length - 1] ?? "—"} hint="latest period" />
        <Stat
          label="Hiring vs base"
          value={lift === null ? "—" : `${lift > 0 ? "+" : ""}${lift}%`}
          hint="job-posting volume"
          tone={lift !== null && lift > 40 ? "warn" : "default"}
        />
        <Stat
          label="Senior hires"
          value={company.seniorHires.length}
          hint="tracked"
          tone={company.seniorHires.some((h) => h.hot) ? "warn" : "default"}
        />
        <Stat label="Backed by" value={FIRMS[company.firm].name} hint={company.stage} />
      </StatRow>

      <div className="mb-6 grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Panel label="About">
          {company.description ? (
            <p className="t-body text-ink-2">{company.description}</p>
          ) : (
            <p className="t-body text-ink-4">No description in source data.</p>
          )}
          {company.sector && (
            <div className="mt-5 border-t border-line-faint pt-4">
              <span className="eyebrow block">Sector</span>
              <span className="mt-2 block t-caption text-ink !max-w-none">
                {company.sector}
              </span>
            </div>
          )}
        </Panel>
        <Panel label="Links">
          {contactRows.length === 0 ? (
            <div className="py-2 font-mono text-meta text-ink-4">
              No public links in source data.
            </div>
          ) : (
            <ContactRows rows={contactRows} />
          )}
        </Panel>
      </div>

      <Panel label="The deal" className="mb-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <DealCell label="Who did the deal">
            {dealPartner ? (
              <button
                onClick={() => setOpen({ kind: "partner", id: dealPartner.id })}
                className="mt-1 flex items-center gap-3 rounded-md border border-line-faint bg-surface-2/40 px-3 py-2 text-left transition-colors hover:border-line-hard"
              >
                <Avatar
                  name={dealPartner.name}
                  color={firmColor(dealPartner.firm)}
                  size="sm"
                  textColor={INK_ON_DARK}
                />
                <span className="flex flex-col">
                  <span className="t-h-sm">{dealPartner.name}</span>
                  <span className="font-mono text-meta text-ink-4">
                    {FIRMS[dealPartner.firm].name} · open profile →
                  </span>
                </span>
              </button>
            ) : (
              <div className="mt-2 n-sm text-ink">{FIRMS[company.firm].name}</div>
            )}
          </DealCell>
          <DealCell label="Amount invested">
            <div className="mt-2 n-sm text-ink">{company.deal.invested || "—"}</div>
            <div className="mt-2 font-mono text-meta tabnum text-ink-4">
              {company.deal.lead ? "led the round" : "participated"}
              {company.deal.round ? ` · ${company.deal.round}` : ""}
            </div>
          </DealCell>
          <DealCell label="Ownership">
            <div className="mt-2 n-sm text-ink">{company.deal.ownership || "—"}</div>
            <div className="mt-2 font-mono text-meta tabnum text-ink-4">estimated from round</div>
          </DealCell>
          <DealCell label="Valuation">
            <div className="mt-2 n-sm text-ink">{company.deal.valuation || "—"}</div>
            <div className="mt-2 font-mono text-meta tabnum text-ink-4">
              {company.deal.dealDate ? `as of ${company.deal.dealDate}` : "date n/a"}
            </div>
          </DealCell>
        </div>
      </Panel>

      {company.note && <Interp>{company.note}</Interp>}

      <div className="mb-6 grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Panel label="Job postings over time">
          <MiniBarChart
            data={company.jobs}
            accent={firmColor(company.firm)}
            base="oklch(33% 0.010 60)"
            highlightFrom={3}
          />
        </Panel>
        <Panel label="Senior hires" pill="orange = fundraise signal">
          {company.seniorHires.length === 0 ? (
            <div className="py-4 font-mono text-meta text-ink-4">No senior hires tracked.</div>
          ) : (
            <Timeline
              items={company.seniorHires.map((h) => ({
                title: h.role,
                description: h.name,
                hot: h.hot,
              }))}
            />
          )}
        </Panel>
      </div>

      {company.foundersList.length > 0 && (
        <Panel label="Founders" className="mb-6">
          <ul className="flex flex-col gap-2">
            {company.foundersList.map((f, i) => (
              <li
                key={`${f.name}-${i}`}
                className="flex items-baseline justify-between gap-3 rounded-md border border-line-faint bg-surface-2/40 px-3 py-2"
              >
                <span className="t-h-sm">{f.name}</span>
                <span className="font-mono text-meta text-ink-4">{f.role || "—"}</span>
              </li>
            ))}
          </ul>
        </Panel>
      )}

      {coTopics.length > 0 && (
        <Panel label={`What ${company.name} is talking about`} pill="orange = newly emphasised" className="mb-6">
          <p className="mb-4 t-caption text-ink-2 !max-w-[68ch]">
            Topic mix derived from public posts, blog and job-listing language. A company
            leaning hard into a theme is its own deal-flow signal, separate from what partners say.
          </p>
          <TopicsList topics={coTopics} />
        </Panel>
      )}

      {relatedSignals.length > 0 && (
        <Panel label={`Tracked signals referencing ${company.name}`}>
          <div className="flex flex-col gap-3">
            {relatedSignals.map((s) => (
              <SignalCard key={s.id} signal={s} compact />
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}

function DealCell({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-line-faint bg-surface-2/40 px-4 py-3">
      <div className="eyebrow">{label}</div>
      {children}
    </div>
  );
}
