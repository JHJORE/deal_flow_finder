"use client";

import { NetworkGraph } from "@/components/NetworkGraph";
import { FOUNDER_AVATAR } from "@/lib/ui";
import { PageHeader } from "@/components/PageHeader";
import { useRadar } from "@/lib/state";

export function GraphsView() {
  const { graphMode, setGraphMode } = useRadar();

  const isTheme = graphMode === "theme";

  return (
    <>
      <PageHeader
        eyebrow="Graphs · attention network"
        title={
          isTheme ? <>Where attention is clustering.</> : <>Who is following whom.</>
        }
        description={
          isTheme
            ? "An engagement network. Theme nodes are hubs; partners cluster around the themes they engage. Bigger node = more people engaging it."
            : "A web of partners and the founders they follow. Clusters show where attention is concentrating, before any conversation has happened."
        }
      />

      <section className="panel px-7 py-7">
        <div className="mb-5 flex flex-wrap items-center gap-4">
          <div className="inline-flex overflow-hidden rounded-md border border-line-faint">
            <button
              onClick={() => setGraphMode("theme")}
              className={`px-4 py-1.5 text-meta font-medium transition-colors ${
                isTheme ? "bg-accent text-surface-0" : "text-ink-3 hover:text-ink"
              }`}
            >
              Theme graph
            </button>
            <button
              onClick={() => setGraphMode("follow")}
              className={`px-4 py-1.5 text-meta font-medium transition-colors ${
                !isTheme ? "bg-accent text-surface-0" : "text-ink-3 hover:text-ink"
              }`}
            >
              Follower graph
            </button>
          </div>
          <span className="font-mono text-meta tabnum text-ink-4">
            {isTheme ? "hub size = partners engaging · click any node to inspect" : "node size = connections · click any node to inspect"}
          </span>
        </div>

        <div className="overflow-hidden rounded-md border border-line-faint">
          <NetworkGraph mode={graphMode} />
        </div>

        <div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 font-mono text-meta text-ink-3">
          {isTheme ? (
            <>
              <Legend swatch="oklch(72% 0.155 50)" label="theme hub" />
              <Legend swatch="var(--firm-sequoia)" label="Sequoia partner" />
              <Legend swatch="var(--firm-a16z)" label="a16z partner" />
              <Legend swatch="var(--firm-yc)" label="YC partner" />
            </>
          ) : (
            <>
              <Legend swatch={FOUNDER_AVATAR} label="founder" />
              <Legend swatch="var(--firm-sequoia)" label="Sequoia partner" />
              <Legend swatch="var(--firm-a16z)" label="a16z partner" />
              <Legend swatch="var(--firm-yc)" label="YC partner" />
            </>
          )}
        </div>
      </section>
    </>
  );
}

function Legend({ swatch, label }: { swatch: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className="h-2.5 w-2.5 rounded-full" style={{ background: swatch }} />
      {label}
    </span>
  );
}
