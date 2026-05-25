"use client";

import {
  FILINGS,
  FIRMS,
  PARTNERS,
  THEMES,
  delta,
  founderById,
} from "@/lib/data";
import { useRadar } from "@/lib/state";
import type { Partner, Signal } from "@/lib/types";
import {
  Fragment,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

type Props = { signals: Signal[] };

type Tok = { text: string; accent?: boolean };
type LineModel = { tokens: Tok[]; node: ReactNode };

// Module-level: a briefing already streamed once in this page session
// should not replay when the view is unmounted and remounted.
let hasStreamedThisSession = false;

const CHAR_DELAY_MS = 5;
const CHAR_JITTER_MS = 4;
const PUNCT_PAUSE: Record<string, number> = { ",": 18, "—": 23, ".": 36, ";": 23 };
const INTER_LINE_PAUSE_MS = 73;
const TAIL_PAUSE_MS = 30;

export function Briefing({ signals }: Props) {
  const { isWatched, activeFirms } = useRadar();

  const liveLines = useMemo(
    () => computeBriefing(signals, isWatched, activeFirms),
    [signals, isWatched, activeFirms]
  );

  // Snapshot the lines we stream so they don't reshuffle mid-animation if
  // filters change. Live updates resume once streaming completes.
  const snapshotRef = useRef<LineModel[] | null>(null);
  const [done, setDone] = useState(() => hasStreamedThisSession);
  const [lineIdx, setLineIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);

  if (!done && snapshotRef.current === null && liveLines.length > 0) {
    snapshotRef.current = liveLines;
  }
  const lines = !done && snapshotRef.current ? snapshotRef.current : liveLines;

  // Honour reduced-motion: jump to the finished state immediately.
  useEffect(() => {
    if (done) return;
    if (typeof window === "undefined") return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (mq.matches) {
      hasStreamedThisSession = true;
      setDone(true);
    }
  }, [done]);

  // The typing ticker.
  useEffect(() => {
    if (done || lines.length === 0) return;
    const line = lines[lineIdx];
    if (!line) return;
    const flat = flattenText(line.tokens);

    if (charIdx >= flat.length) {
      // Line finished. Pause, then either advance or finalize.
      if (lineIdx + 1 >= lines.length) {
        const t = setTimeout(() => {
          hasStreamedThisSession = true;
          setDone(true);
        }, TAIL_PAUSE_MS);
        return () => clearTimeout(t);
      }
      const t = setTimeout(() => {
        setLineIdx((i) => i + 1);
        setCharIdx(0);
      }, INTER_LINE_PAUSE_MS);
      return () => clearTimeout(t);
    }

    const prevChar = charIdx > 0 ? flat[charIdx - 1] : "";
    const delay =
      CHAR_DELAY_MS +
      Math.random() * CHAR_JITTER_MS +
      (PUNCT_PAUSE[prevChar] ?? 0);
    const t = setTimeout(() => setCharIdx((c) => c + 1), delay);
    return () => clearTimeout(t);
  }, [done, lines, lineIdx, charIdx]);

  if (lines.length === 0) return null;

  const status = done
    ? `synthesised from ${signals.length} signals`
    : `synthesising ${signals.length} signals`;

  return (
    <section className="mb-7 rounded-lg border border-line-faint bg-surface-raised px-7 py-6">
      <div className="mb-4 flex items-baseline gap-4">
        <span className="eyebrow-accent">AI briefing</span>
        <span className="font-mono text-meta tabnum text-ink-4">
          {status}
          {!done && <span aria-hidden className="brief-ellipsis" />}
        </span>
      </div>
      <ul className="space-y-3.5" aria-live={done ? "off" : "polite"} aria-busy={!done}>
        {lines.map((l, i) => {
          if (done) {
            return (
              <li key={i} className="flex gap-4">
                <span
                  aria-hidden
                  className="mt-[0.6rem] inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-accent"
                />
                <span className="t-body !max-w-none">{l.node}</span>
              </li>
            );
          }
          if (i > lineIdx) return null;
          const isActive = i === lineIdx;
          const visible = isActive ? charIdx : Number.POSITIVE_INFINITY;
          return (
            <li key={i} className="brief-line-in flex gap-4">
              <span
                aria-hidden
                className="mt-[0.6rem] inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-accent"
              />
              <span className="t-body !max-w-none">
                {renderTokens(l.tokens, visible)}
                {isActive && <span aria-hidden className="brief-caret" />}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function flattenText(tokens: Tok[]): string {
  let s = "";
  for (const t of tokens) s += t.text;
  return s;
}

function renderTokens(tokens: Tok[], visibleChars: number): ReactNode {
  const out: ReactNode[] = [];
  let consumed = 0;
  for (let i = 0; i < tokens.length; i++) {
    if (consumed >= visibleChars) break;
    const t = tokens[i];
    const remaining = visibleChars - consumed;
    const slice = t.text.length <= remaining ? t.text : t.text.slice(0, remaining);
    out.push(
      t.accent ? (
        <Accent key={i}>{slice}</Accent>
      ) : (
        <Fragment key={i}>{slice}</Fragment>
      )
    );
    consumed += t.text.length;
  }
  return <>{out}</>;
}

function Accent({ children }: { children: ReactNode }) {
  return <span style={{ color: "var(--accent)", fontWeight: 600 }}>{children}</span>;
}

function NewTopicLine({ partners }: { partners: Partner[] }) {
  const [expanded, setExpanded] = useState(false);
  const hiddenCount = Math.max(0, partners.length - 3);
  const visible = expanded ? partners : partners.slice(0, 3);
  return (
    <>
      <Accent>
        {partners.length} partner{partners.length === 1 ? "" : "s"}
      </Accent>{" "}
      opened a new topic this period —{" "}
      {visible.map((p, i) => (
        <Fragment key={p.id}>
          {i > 0 && ", "}
          {p.name}
        </Fragment>
      ))}
      {hiddenCount > 0 && !expanded && (
        <>
          {" "}
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className="font-medium text-accent underline-offset-2 hover:underline"
          >
            +{hiddenCount} more
          </button>
        </>
      )}
      {hiddenCount > 0 && expanded && (
        <>
          {" "}
          <button
            type="button"
            onClick={() => setExpanded(false)}
            className="font-medium text-ink-3 underline-offset-2 hover:underline"
          >
            show less
          </button>
        </>
      )}
      .
    </>
  );
}

function computeBriefing(
  sigs: Signal[],
  isWatched: (id: string) => boolean,
  activeFirms: Set<string>
): LineModel[] {
  const lines: LineModel[] = [];

  for (const s of sigs.filter((x) => x.sources.includes("EDGAR"))) {
    const fil = s.filing ? FILINGS[s.filing] : undefined;
    if (!fil) continue;
    const formLabel = fil.formType.split(" — ")[0];
    const firmNames = s.firms.map((f) => FIRMS[f].name).join(" & ");
    const founder = s.actors.map((a) => founderById(a)).find(Boolean);

    const tokens: Tok[] = [
      { text: "EDGAR " },
      { text: formLabel, accent: true },
      { text: ` · ${firmNames} named in ` },
      { text: fil.issuer, accent: true },
      { text: ", not on the public portfolio" },
    ];
    if (founder) tokens.push({ text: `; issuer profile matches ${founder.name}` });
    tokens.push({ text: "." });

    lines.push({
      tokens,
      node: (
        <>
          EDGAR <Accent>{formLabel}</Accent> · {firmNames} named in{" "}
          <Accent>{fil.issuer}</Accent>, not on the public portfolio
          {founder && <>; issuer profile matches {founder.name}</>}.
        </>
      ),
    });
  }

  const convs = sigs.filter((s) => s.headline.toLowerCase().startsWith("convergence"));
  if (convs.length > 0) {
    const names = convs
      .map((s) => {
        const f = s.actors.map((a) => founderById(a)).find(Boolean);
        return f ? f.name : null;
      })
      .filter(Boolean) as string[];
    const eventLabel = `${convs.length} partner-on-founder convergence event${
      convs.length === 1 ? "" : "s"
    }`;
    const tokens: Tok[] = [
      { text: eventLabel, accent: true },
      { text: " open" },
    ];
    if (names.length) tokens.push({ text: ` — ${names.join(", ")}` });
    tokens.push({ text: "." });

    lines.push({
      tokens,
      node: (
        <>
          <Accent>{eventLabel}</Accent> open{names.length ? ` — ${names.join(", ")}` : ""}.
        </>
      ),
    });
  }

  const movers = THEMES.map((t) => {
    const d = delta(t.share);
    return { label: t.label, last: d[d.length - 1] };
  })
    .filter((m) => m.last !== 0)
    .sort((a, b) => Math.abs(b.last) - Math.abs(a.last))
    .slice(0, 3);
  if (movers.length > 0) {
    const top = movers
      .map((m) => `${m.label} ${m.last > 0 ? "+" : ""}${m.last}pts`)
      .join(", ");
    lines.push({
      tokens: [
        { text: "Theme drift this period — " },
        { text: top, accent: true },
        { text: "." },
      ],
      node: (
        <>
          Theme drift this period — <Accent>{top}</Accent>.
        </>
      ),
    });
  }

  const newTopicPartners = PARTNERS.filter(
    (p) => p.newTopic && activeFirms.has(p.firm)
  );
  if (newTopicPartners.length > 0) {
    const total = newTopicPartners.length;
    const visibleNames = newTopicPartners.slice(0, 3).map((p) => p.name).join(", ");
    const hidden = Math.max(0, total - 3);
    const tokens: Tok[] = [
      { text: `${total}`, accent: true },
      { text: ` partner${total === 1 ? "" : "s"} opened a new topic this period — ${visibleNames}` },
    ];
    if (hidden > 0) tokens.push({ text: ` +${hidden} more.` });
    else tokens.push({ text: "." });

    lines.push({
      tokens,
      node: <NewTopicLine partners={newTopicPartners} />,
    });
  }

  const watched = sigs.filter((s) => {
    const onActor = s.actors.some((a) => isWatched(a));
    const onCompany =
      s.filing &&
      FILINGS[s.filing] &&
      isWatched(FILINGS[s.filing].relatedCompany ?? "");
    return onActor || onCompany;
  });
  if (watched.length > 0) {
    const label = `${watched.length} signal${watched.length === 1 ? "" : "s"}`;
    lines.push({
      tokens: [
        { text: label, accent: true },
        { text: " touch your watchlist." },
      ],
      node: (
        <>
          <Accent>{label}</Accent> touch your watchlist.
        </>
      ),
    });
  }

  return lines;
}
