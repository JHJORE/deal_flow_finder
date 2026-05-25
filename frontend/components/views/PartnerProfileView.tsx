"use client";

import { Avatar } from "@/components/Avatar";
import { INK_ON_DARK, INK_ON_LIGHT, FOUNDER_AVATAR } from "@/lib/ui";
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
import { MiniBarChart, MiniLineChart } from "@/components/MiniChart";
import {
  FIRMS,
  FOLLOWS,
  getPartnerBeliefs,
  PERIODS,
  TOP_POSTS,
  actorById,
  computePredictability,
  firmColor,
  founderById,
  partnerById,
  themeByKey,
} from "@/lib/data";
import { useRadar } from "@/lib/state";
import { useMemo, useState } from "react";

export function PartnerProfileView({ id }: { id: string }) {
  const entity = actorById(id);
  if (!entity) return null;
  const partner = partnerById(id);
  const founder = founderById(id);
  const isPartner = !!partner;

  const posts = entity.posts;
  const er = entity.engageRate;
  const baseP = (posts[0] + posts[1] + posts[2]) / 3;
  const baseE = (er[0] + er[1] + er[2]) / 3;
  const liftP = baseP > 0 ? Math.round(((posts[posts.length - 1] - baseP) / baseP) * 100) : 0;
  const liftE = baseE > 0 ? Math.round(((er[er.length - 1] - baseE) / baseE) * 100) : 0;

  return (
    <div className="view-in">
      <BackButton />
      <ProfileHeader
        avatar={
          <Avatar
            name={entity.name}
            color={isPartner ? firmColor(partner!.firm) : FOUNDER_AVATAR}
            size="xl"
            textColor={isPartner ? INK_ON_DARK : INK_ON_LIGHT}
            photoUrl={isPartner ? partner!.photoUrl : null}
          />
        }
        name={entity.name}
        role={
          isPartner
            ? `${FIRMS[partner!.firm].name} · ${partner!.role}`
            : (founder!.role)
        }
        handle={!isPartner ? founder!.handle : undefined}
        rightSlot={<WatchButton id={id} />}
      />

      <PartnerStats partnerId={id} isPartner={isPartner} liftP={liftP} liftE={liftE} />

      {isPartner ? <AboutContact partnerId={id} /> : <FounderContact founderId={id} />}

      <Interp>
        <Interpretation partnerId={id} liftP={liftP} liftE={liftE} />
      </Interp>

      {isPartner && getPartnerBeliefs(id) && <BeliefsPanel partnerId={id} />}

      {isPartner && TOP_POSTS[id] && <TopPostPanel partnerId={id} />}

      <div className="mb-6 grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Panel label={`Posting cadence — posts / month`}>
          <MiniBarChart
            data={posts}
            accent={isPartner ? firmColor(partner!.firm) : "oklch(72% 0.155 50)"}
            base="oklch(33% 0.010 60)"
            highlightFrom={3}
          />
        </Panel>
        <Panel label="Engagement rate — replies + likes">
          <MiniLineChart data={er} accent="var(--accent)" />
        </Panel>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Panel label="Topic mix & change" pill="orange = new">
          <TopicsList topics={entity.topics} />
        </Panel>
        <RelationshipsPanel id={id} isPartner={isPartner} />
      </div>
    </div>
  );
}

function PartnerStats({
  partnerId,
  isPartner,
  liftP,
  liftE,
}: {
  partnerId: string;
  isPartner: boolean;
  liftP: number;
  liftE: number;
}) {
  const { predWindow } = useRadar();
  const entity = actorById(partnerId)!;
  const partner = partnerById(partnerId);

  if (isPartner) {
    const pred = computePredictability(partner!.id, predWindow);
    const predDisplay = pred?.hasDeals ? `${pred.pct}%` : "—";
    const predTone: "default" | "up" | "warn" | "down" = !pred?.hasDeals
      ? "default"
      : pred!.pct >= 70
      ? "up"
      : pred!.pct >= 40
      ? "warn"
      : "down";
    const er = partner!.engageRate;
    const baseE = (er[0] + er[1] + er[2]) / 3;
    const hasActivity = baseE > 0;
    return (
      <StatRow>
        <Stat label="Predictability" value={predDisplay} hint={pred?.hasDeals ? "thesis-to-deals match" : "no led deals yet"} tone={predTone} />
        <Stat label="Posts / month" value={hasActivity ? partner!.posts[partner!.posts.length - 1] : "—"} hint={hasActivity ? "latest period" : "not yet tracked"} />
        <Stat label="Engagement vs base" value={hasActivity ? `${liftE > 0 ? "+" : ""}${liftE}%` : "—"} hint="reply + like rate" tone={hasActivity && liftE > 40 ? "warn" : "default"} />
        <Stat label="Activity" value={partner!.spike ? "Spiking" : hasActivity ? "Steady" : "—"} hint="vs trailing baseline" tone={partner!.spike ? "warn" : "default"} />
      </StatRow>
    );
  }
  const founder = entity as any;
  const partnerFollows = FOLLOWS.filter((x) => x.founder === partnerId).length;
  return (
    <StatRow>
      <Stat label="Posts / month" value={founder.posts[founder.posts.length - 1]} hint="latest period" />
      <Stat label="Posting vs base" value={`${liftP > 0 ? "+" : ""}${liftP}%`} hint="volume" tone="up" />
      <Stat label="Follower growth" value={founder.followerGrowth} hint="trailing 90d" tone="up" />
      <Stat label="Partner follows" value={partnerFollows} hint="tracked partners" tone="warn" />
    </StatRow>
  );
}

function AboutContact({ partnerId }: { partnerId: string }) {
  const p = partnerById(partnerId)!;
  const [expanded, setExpanded] = useState(false);
  const isLong = p.about.length > 320;
  return (
    <div className="mb-6 grid grid-cols-1 gap-5 lg:grid-cols-2">
      <Panel label="About">
        <p className={`t-body text-ink-2 ${isLong && !expanded ? "line-clamp-5" : ""}`}>
          {p.about}
        </p>
        {isLong && (
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="mt-2 font-mono text-meta text-accent hover:underline"
          >
            {expanded ? "Show less" : "Show more"}
          </button>
        )}
        <div className="mt-5 border-t border-line-faint pt-4">
          <span className="eyebrow block">Typical deals</span>
          <span className="mt-2 block t-caption text-ink !max-w-none">{p.checkSize}</span>
        </div>
      </Panel>
      <Panel label="Contact">
        <ContactRows
          rows={[
            p.contact.email !== ""
              ? { key: "Email", value: p.contact.email, href: `mailto:${p.contact.email}` }
              : { key: "Email", value: "—" },
            { key: "Phone", value: p.contact.phone },
            p.contact.linkedin !== ""
              ? { key: "LinkedIn", value: p.contact.linkedin, href: `https://${p.contact.linkedin}` }
              : { key: "LinkedIn", value: "—" },
            p.contact.x !== ""
              ? { key: "X", value: p.contact.x, href: `https://x.com/${p.contact.x.replace("@", "")}` }
              : { key: "X", value: "—" },
          ]}
        />
      </Panel>
    </div>
  );
}

function FounderContact({ founderId }: { founderId: string }) {
  const f = founderById(founderId)!;
  const handle = f.handle.replace(/^@/, "");
  return (
    <div className="mb-6">
      <Panel label="Contact" pill="coming soon">
        <ContactRows
          rows={[
            handle
              ? { key: "X", value: f.handle, href: `https://x.com/${handle}` }
              : { key: "X", value: "—" },
            { key: "Email", value: "—" },
            { key: "Phone", value: "—" },
            { key: "LinkedIn", value: "—" },
          ]}
        />
      </Panel>
    </div>
  );
}

function Interpretation({
  partnerId,
  liftP,
  liftE,
}: {
  partnerId: string;
  liftP: number;
  liftE: number;
}) {
  const partner = partnerById(partnerId);
  const founder = founderById(partnerId);
  if (partner) {
    const er = partner.engageRate;
    const baseE = (er[0] + er[1] + er[2]) / 3;
    if (baseE === 0) {
      return (
        <>
          {`${partner.name} is on the ${partner.stage === "growth" ? "growth" : partner.stage === "both" ? "seed/early and growth" : "seed/early"} team. Posting and engagement aren't tracked yet, so there's no behavioural signal to interpret.`}
        </>
      );
    }
    if (partner.spike) {
      const newTopicLine = partner.newTopic
        ? ` The shift to watch: ${partner.name} has started talking about "${partner.newTopic}" this period, a topic absent from their feed before. A new topic entering a partner feed is the leading indicator of where they want to deploy next.`
        : " A normally steadier partner getting this active often precedes an active process.";
      return (
        <>
          {`${partner.name}'s engagement is running ${liftE > 0 ? "+" : ""}${liftE}% above baseline.`}
          {newTopicLine}
        </>
      );
    }
    return (
      <>
        {`${partner.name} posts at a steady cadence with engagement near baseline.`}
        {partner.newTopic
          ? ` The shift to watch: a new topic — "${partner.newTopic}" — has entered the feed.`
          : " No behavioural anomaly right now; the topic mix below is where a shift would show first."}
      </>
    );
  }
  if (founder) {
    return (
      <>
        {`${founder.name} shows ${liftP > 0 ? "+" : ""}${liftP}% posting acceleration and ${founder.followerGrowth} follower growth. With the partner follows on the right, this is a founder warming up to raise.`}
      </>
    );
  }
  return null;
}

function BeliefsPanel({ partnerId }: { partnerId: string }) {
  const { predWindow, setPredWindow, setOpen } = useRadar();
  const partner = partnerById(partnerId)!;
  const bd = getPartnerBeliefs(partnerId);
  const pred = computePredictability(partnerId, predWindow);
  if (!bd || !pred) return null;

  const { scored, backedCount, hasDeals, pct, total } = pred;

  let scoreLabel: string;
  let scoreColor: string;
  let scoreNote: string;

  if (!hasDeals) {
    scoreLabel = "Not yet measurable";
    scoreColor = "var(--ink-3)";
    scoreNote = `This partner has not personally led a tracked deal${
      predWindow === "90" ? " in the last 90 days" : ""
    }, so their beliefs cannot be checked against revealed behaviour. The stated beliefs below are still a directional guide.`;
  } else if (pct >= 70) {
    scoreLabel = "Highly predictable";
    scoreColor = "var(--positive)";
    scoreNote = "What this partner says publicly closely matches the deals they actually lead. Their stated thesis is a reliable guide to where their next checks go.";
  } else if (pct >= 40) {
    scoreLabel = "Partially predictable";
    scoreColor = "var(--caution)";
    scoreNote = "Some of this partner's public stances show up in their led deals, but not all. Trust the matched beliefs more than the unmatched ones as a sourcing signal.";
  } else {
    scoreLabel = "Low predictability";
    scoreColor = "var(--negative)";
    scoreNote = "This partner's public writing and their actual led deals diverge. Watch what they fund, not what they post — the gap itself is the signal.";
  }

  const confirmations = scored.filter((b) => hasDeals && b.backedBy);
  const contradictions = scored.filter((b) => hasDeals && !b.backedBy);
  const ordered = [...scored.filter((b) => b.era === "recent"), ...scored.filter((b) => b.era === "longheld")];

  return (
    <Panel label="Beliefs & predictability" className="mb-6">
      <p className="mb-5 t-body !max-w-[68ch]">{bd.summary}</p>

      <div
        className="mb-5 flex flex-wrap items-baseline gap-4 rounded-md bg-surface-raised px-5 py-4"
        style={{ outline: `1px solid color-mix(in oklch, ${scoreColor} 35%, transparent)` }}
      >
        <span className="n-lg" style={{ color: scoreColor }}>
          {hasDeals ? `${pct}%` : "—"}
        </span>
        <span className="t-h-sm" style={{ color: scoreColor }}>
          Predictability: {scoreLabel}
        </span>
        <span className="ml-auto inline-flex overflow-hidden rounded-md border border-line">
          <button
            onClick={() => setPredWindow("all")}
            className={`px-3 py-1 text-meta font-semibold transition-colors ${
              predWindow === "all" ? "bg-accent text-surface-0" : "text-ink-3 hover:text-ink"
            }`}
          >
            All time
          </button>
          <button
            onClick={() => setPredWindow("90")}
            className={`px-3 py-1 text-meta font-semibold transition-colors ${
              predWindow === "90" ? "bg-accent text-surface-0" : "text-ink-3 hover:text-ink"
            }`}
          >
            Last 90d
          </button>
        </span>
        <p className="basis-full t-caption !max-w-none text-ink-2">
          {scoreNote}
          {hasDeals && (
            <>
              {" "}
              <strong className="font-semibold text-ink">
                {backedCount} of {total}
              </strong>{" "}
              beliefs are backed by a specific deal they led
              {predWindow === "90" ? " in the last 90 days" : ""}.
            </>
          )}
        </p>
      </div>

      {hasDeals && (
        <div className="mb-5 flex flex-wrap gap-5 rounded-md bg-surface-2/40 px-4 py-3">
          <span className="inline-flex items-center gap-2 text-meta text-ink-2">
            <span className="h-2 w-2 rounded-full bg-positive" />
            {confirmations.length} confirmed by a led deal
          </span>
          <span className="inline-flex items-center gap-2 text-meta text-ink-2">
            <span className="h-2 w-2 rounded-full bg-negative" />
            {contradictions.length} contradicted — said but not funded
          </span>
        </div>
      )}

      <div className="overflow-hidden rounded-md border border-line-faint">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-surface-raised">
              <th className="px-4 py-3 text-left eyebrow !text-ink-4">
                Public view — what they say
              </th>
              <th className="px-4 py-3 text-left eyebrow !text-ink-4">Era</th>
              <th className="px-4 py-3 text-left eyebrow !text-ink-4">Source</th>
              <th className="px-4 py-3 text-left eyebrow !text-ink-4">Deal evidence</th>
            </tr>
          </thead>
          <tbody>
            {ordered.map((b, i) => {
              const eraLabel = b.era === "recent" ? "Recent" : "Long-held";
              let verdict: React.ReactNode;
              let rowTint = "";
              let dotColor = "var(--ink-4)";
              if (!hasDeals) {
                verdict = <span className="font-mono text-meta text-ink-4">No deal data yet</span>;
              } else if (b.backedBy) {
                verdict = (
                  <button
                    onClick={() => setOpen({ kind: "company", id: b.backedBy!.id })}
                    className="inline-flex items-center gap-1.5 rounded-sm bg-positive/15 px-2.5 py-1 font-mono text-meta tabnum text-positive transition-colors hover:bg-positive/25"
                  >
                    ✓ Confirmed — {b.backedBy.name} →
                  </button>
                );
                rowTint = "bg-positive/[0.04]";
                dotColor = "var(--positive)";
              } else {
                verdict = (
                  <span className="inline-flex items-center gap-1.5 rounded-sm border border-negative/40 bg-negative/10 px-2 py-1 font-mono text-meta text-negative">
                    ⚠ Contradicted — no led deal backs this
                  </span>
                );
                rowTint = "bg-negative/[0.04]";
                dotColor = "var(--negative)";
              }
              return (
                <tr key={i} className={`${rowTint} border-t border-line-faint`}>
                  <td className="px-4 py-3 align-top t-caption !max-w-none text-ink">
                    <span className="mr-2 inline-block h-2 w-2 rounded-full align-middle" style={{ background: dotColor }} />
                    {b.text}
                  </td>
                  <td className="px-4 py-3 align-top">
                    <span
                      className={`inline-block rounded-sm border px-2 py-0.5 font-mono text-eyebrow font-bold uppercase ${
                        b.era === "recent" ? "border-accent text-accent" : "border-line text-ink-3"
                      }`}
                    >
                      {eraLabel}
                    </span>
                  </td>
                  <td className="px-4 py-3 align-top font-mono text-meta tabnum text-ink-3">
                    {b.sources.join(", ")}
                  </td>
                  <td className="px-4 py-3 align-top">{verdict}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function TopPostPanel({ partnerId }: { partnerId: string }) {
  const p = partnerById(partnerId)!;
  const tp = TOP_POSTS[partnerId];
  return (
    <Panel label="Most-engaged recent post" pill="live from X" className="mb-6">
      <div className="flex items-start gap-4">
        <Avatar
          name={p.name}
          color={firmColor(p.firm)}
          size="md"
          textColor={INK_ON_DARK}
          photoUrl={p.photoUrl}
        />
        <div className="grow">
          <div className="flex flex-wrap items-baseline gap-2">
            <span className="t-h-sm">{p.name}</span>
            <span className="font-mono text-meta tabnum text-ink-4">{p.contact.x}</span>
            <span className="ml-auto font-mono text-meta tabnum text-ink-4">{tp.when}</span>
          </div>
          <p className="mt-2 t-body !max-w-[60ch]">{tp.text}</p>
          <div className="mt-3 flex items-center gap-5 font-mono text-meta tabnum text-ink-3">
            <span>♥ {tp.likes}</span>
            <span>↻ {tp.reposts}</span>
          </div>
        </div>
      </div>
    </Panel>
  );
}

function RelationshipsPanel({ id, isPartner }: { id: string; isPartner: boolean }) {
  const RECENT_FROM = 3;
  let items: { date?: string; title: string; description: string; hot?: boolean; flag?: string }[];
  let title: string;
  if (isPartner) {
    const fs = FOLLOWS.filter((x) => x.partner === id).sort((a, b) => b.firstSeen - a.firstSeen);
    title = "Founders this partner started following";
    items = fs.map((x) => {
      const fo = founderById(x.founder);
      const isNew = x.firstSeen >= RECENT_FROM;
      return {
        date: `${isNew ? "" : ""}first follow · ${PERIODS[x.firstSeen]}`,
        title: fo ? fo.name : x.founder,
        description: fo ? fo.role : "",
        hot: false,
        flag: isNew ? "NEW" : undefined,
      };
    });
  } else {
    const fs = FOLLOWS.filter((x) => x.founder === id).sort((a, b) => b.firstSeen - a.firstSeen);
    title = "Partners who started following this founder";
    items = fs.map((x) => {
      const pa = partnerById(x.partner)!;
      const isNew = x.firstSeen >= RECENT_FROM;
      return {
        date: `first follow · ${PERIODS[x.firstSeen]}`,
        title: pa.name,
        description: `${actorById(x.partner) ? "" : ""}${pa.role}`,
        hot: false,
        flag: isNew ? "NEW" : undefined,
      };
    });
  }
  const newCount = items.filter((i) => i.flag === "NEW").length;

  return (
    <Panel label={title} pill={newCount > 0 ? `${newCount} new in 90d` : undefined}>
      {items.length === 0 ? (
        <div className="py-4 font-mono text-meta text-ink-4">No tracked follows yet.</div>
      ) : (
        <Timeline items={items} />
      )}
    </Panel>
  );
}
