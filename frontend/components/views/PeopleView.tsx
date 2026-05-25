"use client";

import { Avatar } from "@/components/Avatar";
import { INK_ON_DARK, INK_ON_LIGHT, FOUNDER_AVATAR } from "@/lib/ui";
import { PageHeader } from "@/components/PageHeader";
import { FIRMS, FOUNDERS, PARTNERS, firmColor } from "@/lib/data";
import { useRadar } from "@/lib/state";
import type { Founder, Partner } from "@/lib/types";

export function PeopleView() {
  const { activeFirms, setOpen, isWatched, peopleTab, setPeopleTab } = useRadar();
  const isPartners = peopleTab === "partners";
  const ps = PARTNERS.filter((p) => activeFirms.has(p.firm));

  return (
    <>
      <PageHeader eyebrow="People watch" showFirmFilter={isPartners} />

      <div className="mb-6 inline-flex overflow-hidden rounded-md border border-line-faint">
        <button
          onClick={() => setPeopleTab("partners")}
          className={`px-4 py-1.5 text-meta font-medium transition-colors ${
            isPartners ? "bg-accent text-surface-0" : "text-ink-3 hover:text-ink"
          }`}
        >
          Partners
        </button>
        <button
          onClick={() => setPeopleTab("founders")}
          className={`px-4 py-1.5 text-meta font-medium transition-colors ${
            !isPartners ? "bg-accent text-surface-0" : "text-ink-3 hover:text-ink"
          }`}
        >
          Founders
        </button>
      </div>

      {isPartners ? (
        ps.length === 0 ? (
          <Empty kind="partners" />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {ps.map((p) => (
              <PartnerCard
                key={p.id}
                partner={p}
                watched={isWatched(p.id)}
                onOpen={() => setOpen({ kind: "partner", id: p.id })}
              />
            ))}
          </div>
        )
      ) : FOUNDERS.length === 0 ? (
        <Empty kind="founders" />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FOUNDERS.map((f) => (
            <FounderCard
              key={f.id}
              founder={f}
              watched={isWatched(f.id)}
              onOpen={() => setOpen({ kind: "partner", id: f.id })}
            />
          ))}
        </div>
      )}
    </>
  );
}

function PartnerCard({ partner, onOpen, watched }: { partner: Partner; onOpen: () => void; watched: boolean }) {
  const er = partner.engageRate;
  const base = (er[0] + er[1] + er[2]) / 3;
  const hasActivity = base > 0;
  const lift = hasActivity ? Math.round(((er[er.length - 1] - base) / base) * 100) : 0;
  const liftDisplay = hasActivity ? `${lift > 0 ? "+" : ""}${lift}%` : "—";
  const postsDisplay = hasActivity ? partner.posts[partner.posts.length - 1] : "—";
  return (
    <button
      onClick={onOpen}
      className="group card-lift flex flex-col gap-3 rounded-lg border border-line-faint bg-surface-1 px-5 py-5 text-left hover:border-line-hard"
    >
      <div className="flex items-center gap-3">
        <Avatar
          name={partner.name}
          color={firmColor(partner.firm)}
          size="md"
          textColor={INK_ON_DARK}
          watched={watched}
        />
        <div>
          <div className="t-h-sm">{partner.name}</div>
          <div className="t-meta">
            {FIRMS[partner.firm].name} · {partner.role}
          </div>
        </div>
      </div>

      <p className="t-caption !max-w-none line-clamp-2 min-h-[3em] text-ink-2">
        {partner.focus || (partner.stage ? "Focus not yet tracked." : "")}
      </p>

      {partner.newTopic ? (
        <div className="font-mono text-meta tabnum text-accent">
          + newly talking about {partner.newTopic}
        </div>
      ) : (
        <div className="font-mono text-meta text-ink-4">— no new topic</div>
      )}

      <div className="mt-1 grid grid-cols-3 gap-4 border-t border-line-faint pt-4">
        <Stat label="posts / mo" value={postsDisplay} />
        <Stat
          label="engage vs base"
          value={liftDisplay}
          tone={hasActivity && lift > 40 ? "warn" : "default"}
        />
        <Stat label="spiking" value={partner.spike ? "Yes" : "No"} tone={partner.spike ? "warn" : "default"} />
      </div>
    </button>
  );
}

function FounderCard({ founder, onOpen, watched }: { founder: Founder; onOpen: () => void; watched: boolean }) {
  const er = founder.engageRate;
  const base = (er[0] + er[1] + er[2]) / 3;
  const lift = Math.round(((er[er.length - 1] - base) / base) * 100);
  const topTopic = [...founder.topics].sort((a, b) => b.w - a.w)[0]?.t ?? founder.role;
  const newTopic = founder.topics.find((t) => t.isNew)?.t ?? null;
  const growthNum = parseInt(founder.followerGrowth.replace(/[^0-9-]/g, ""), 10);
  const growthHot = !Number.isNaN(growthNum) && growthNum >= 100;
  return (
    <button
      onClick={onOpen}
      className="group card-lift flex flex-col gap-3 rounded-lg border border-line-faint bg-surface-1 px-5 py-5 text-left hover:border-line-hard"
    >
      <div className="flex items-center gap-3">
        <Avatar
          name={founder.name}
          color={FOUNDER_AVATAR}
          size="md"
          textColor={INK_ON_LIGHT}
          watched={watched}
        />
        <div>
          <div className="t-h-sm">{founder.name}</div>
          <div className="t-meta">
            {founder.handle} · {founder.role}
          </div>
        </div>
      </div>

      <p className="t-caption !max-w-none line-clamp-2 min-h-[3em] text-ink-2">
        Focus: {topTopic}
      </p>

      {newTopic ? (
        <div className="font-mono text-meta tabnum text-accent">
          + newly talking about {newTopic}
        </div>
      ) : (
        <div className="font-mono text-meta text-ink-4">— no new topic</div>
      )}

      <div className="mt-1 grid grid-cols-3 gap-4 border-t border-line-faint pt-4">
        <Stat label="posts / mo" value={founder.posts[founder.posts.length - 1]} />
        <Stat
          label="engage vs base"
          value={`${lift > 0 ? "+" : ""}${lift}%`}
          tone={lift > 40 ? "warn" : "default"}
        />
        <Stat
          label="follower growth"
          value={founder.followerGrowth}
          tone={growthHot ? "warn" : "default"}
        />
      </div>
    </button>
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

function Empty({ kind }: { kind: "partners" | "founders" }) {
  return (
    <div className="rounded-lg border border-line-faint bg-surface-1 px-6 py-12 text-center text-caption text-ink-3">
      {kind === "partners" ? "No partners in this filter." : "No founders to show."}
    </div>
  );
}
