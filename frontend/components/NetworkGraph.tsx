"use client";

import {
  FIRMS,
  FOLLOWS,
  PARTNERS,
  THEMES,
  FOUNDERS,
  firmColor,
  founderById,
  initials,
  partnerById,
  themeByKey,
  themeColor,
} from "@/lib/data";
import { INK_ON_DARK, INK_ON_LIGHT, FOUNDER_AVATAR } from "@/lib/ui";
import { useRadar } from "@/lib/state";
import type { Theme, ThemeKey } from "@/lib/types";
import { useMemo, useState } from "react";

type Mode = "theme" | "follow";

const SVG_W = 900;
const SVG_H = 520;

// stagger budgets — total under 800ms regardless of node count
const EDGE_STEP_MS = 12;
const NODE_STEP_MS = 24;
const NODE_BASE_MS = 240; // wait for edges to finish establishing before nodes appear
const LABEL_BASE_MS = 480;

type Node = {
  id: string;
  type: "theme" | "partner" | "founder";
  r: number;
  x: number;
  y: number;
  // payload
  theme?: Theme;
  pid?: string;
  fid?: string;
};

type Link = { a: string; b: string; len: number };

export function NetworkGraph({ mode }: { mode: Mode }) {
  const { activeFirms, setSelectedTheme, setView, setOpen } = useRadar();
  const [hovered, setHovered] = useState<string | null>(null);
  const [flashing, setFlashing] = useState<string | null>(null);

  const layout = useMemo(() => {
    if (mode === "theme") return computeThemeGraph(activeFirms);
    return computeFollowerGraph(activeFirms);
  }, [mode, activeFirms]);

  // build the set of nodes connected to the hovered one (including itself).
  // when nothing is hovered the set is null and everything renders at full intensity.
  const connectedSet = useMemo<Set<string> | null>(() => {
    if (!hovered) return null;
    const s = new Set<string>([hovered]);
    layout.links.forEach((l) => {
      if (l.a === hovered) s.add(l.b);
      if (l.b === hovered) s.add(l.a);
    });
    return s;
  }, [hovered, layout.links]);

  // largest theme hub — gets the slow breathing animation in theme mode
  const breathingHubId = useMemo(() => {
    if (mode !== "theme") return null;
    let best: Node | null = null;
    layout.nodes.forEach((n) => {
      if (n.type !== "theme") return;
      if (!best || n.r > best.r) best = n;
    });
    return best ? (best as Node).id : null;
  }, [mode, layout.nodes]);

  if (layout.nodes.length === 0) {
    return (
      <div className="flex h-[400px] items-center justify-center text-meta text-ink-4">
        No graph in current filter.
      </div>
    );
  }

  const byId = Object.fromEntries(layout.nodes.map((n) => [n.id, n]));

  function flashAndRun(id: string, run: () => void) {
    setFlashing(id);
    setTimeout(() => {
      setFlashing(null);
      run();
    }, 220);
  }

  function onThemeClick(key: ThemeKey) {
    setSelectedTheme(key);
    setView("consensus");
  }

  return (
    <svg
      viewBox={`0 0 ${SVG_W} ${SVG_H}`}
      className="block w-full"
      role="img"
      aria-label={mode === "theme" ? "Theme graph" : "Follower graph"}
      style={{ background: "var(--surface-0)" }}
    >
      <defs>
        <radialGradient id="hub-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="oklch(72% 0.155 50 / 0.18)" />
          <stop offset="100%" stopColor="oklch(72% 0.155 50 / 0)" />
        </radialGradient>
      </defs>

      {/* edges */}
      {layout.links.map((l, i) => {
        const a = byId[l.a];
        const b = byId[l.b];
        if (!a || !b) return null;
        const touchesHover =
          !connectedSet || (connectedSet.has(l.a) && connectedSet.has(l.b));
        const baseOpacity = touchesHover ? 0.42 : 0.06;
        const strokeColor =
          hovered && touchesHover ? "oklch(72% 0.05 60)" : "oklch(50% 0.012 60)";
        return (
          <line
            key={`${l.a}-${l.b}-${i}`}
            className="graph-edge"
            x1={a.x}
            y1={a.y}
            x2={b.x}
            y2={b.y}
            stroke={strokeColor}
            strokeWidth={hovered && touchesHover ? 1.4 : 0.8}
            style={{
              animationDelay: `${i * EDGE_STEP_MS}ms`,
              opacity: baseOpacity,
              ["--edge-opacity" as any]: baseOpacity,
            }}
          />
        );
      })}

      {/* theme hubs */}
      {layout.nodes
        .filter((n) => n.type === "theme")
        .map((n, i) => {
          const t = n.theme!;
          const isHovered = hovered === n.id;
          const dim = connectedSet && !connectedSet.has(n.id);
          const breathing = breathingHubId === n.id;
          return (
            <g
              key={n.id}
              className={`graph-node cursor-pointer ${flashing === n.id ? "node-click-flash" : ""}`}
              style={{
                animationDelay: `${NODE_BASE_MS + i * NODE_STEP_MS}ms`,
                opacity: dim ? 0.18 : 1,
              }}
              onMouseEnter={() => setHovered(n.id)}
              onMouseLeave={() => setHovered((cur) => (cur === n.id ? null : cur))}
              onClick={() => flashAndRun(n.id, () => onThemeClick(t.key))}
            >
              <circle
                cx={n.x}
                cy={n.y}
                r={n.r + 12}
                fill="url(#hub-glow)"
                className={breathing ? "hub-breath" : ""}
                style={breathing ? { transformOrigin: `${n.x}px ${n.y}px` } : undefined}
              />
              <circle
                cx={n.x}
                cy={n.y}
                r={n.r}
                fill={themeColor(t)}
                fillOpacity={isHovered ? 0.2 : 0.12}
                stroke={themeColor(t)}
                strokeWidth={isHovered ? 2 : 1.4}
              />
              <circle cx={n.x} cy={n.y} r={5} fill={themeColor(t)} />
              <text
                x={n.x}
                y={n.y + n.r + 18}
                textAnchor="middle"
                fontFamily="var(--font-display)"
                fontSize="12.5"
                fontWeight={600}
                fill={themeColor(t)}
                opacity={dim ? 0 : 1}
                style={{ pointerEvents: "none", transition: "opacity 180ms ease" }}
              >
                {t.label}
              </text>
            </g>
          );
        })}

      {/* partner & founder nodes */}
      {layout.nodes
        .filter((n) => n.type === "partner")
        .map((n, i) => {
          const p = partnerById(n.pid!);
          if (!p) return null;
          const col = firmColor(p.firm);
          const isHovered = hovered === n.id;
          const dim = connectedSet && !connectedSet.has(n.id);
          return (
            <g
              key={n.id}
              className={`graph-node cursor-pointer ${flashing === n.id ? "node-click-flash" : ""}`}
              style={{
                animationDelay: `${NODE_BASE_MS + (i + 8) * NODE_STEP_MS}ms`,
                opacity: dim ? 0.22 : 1,
              }}
              onMouseEnter={() => setHovered(n.id)}
              onMouseLeave={() => setHovered((cur) => (cur === n.id ? null : cur))}
              onClick={() => flashAndRun(n.id, () => setOpen({ kind: "partner", id: p.id }))}
            >
              {isHovered && (
                <circle
                  cx={n.x}
                  cy={n.y}
                  r={n.r + 4}
                  fill="none"
                  stroke={col}
                  strokeWidth={1.2}
                  strokeOpacity={0.7}
                />
              )}
              <circle
                cx={n.x}
                cy={n.y}
                r={n.r}
                fill={col}
                stroke="var(--surface-0)"
                strokeWidth={2.5}
              />
              <text
                x={n.x}
                y={n.y + 3}
                textAnchor="middle"
                fontFamily="var(--font-display)"
                fontSize={Math.max(8.5, n.r * 0.7)}
                fontWeight={700}
                fill={INK_ON_DARK}
                style={{ pointerEvents: "none" }}
              >
                {initials(p.name)}
              </text>
              <NodeLabel
                x={n.x}
                y={n.y - n.r - 10}
                text={p.name}
                subtle={false}
                delay={LABEL_BASE_MS + i * NODE_STEP_MS}
                hidden={!!dim}
              />
            </g>
          );
        })}

      {layout.nodes
        .filter((n) => n.type === "founder")
        .map((n, i) => {
          const f = founderById(n.fid!);
          if (!f) return null;
          const isHovered = hovered === n.id;
          const dim = connectedSet && !connectedSet.has(n.id);
          return (
            <g
              key={n.id}
              className={`graph-node cursor-pointer ${flashing === n.id ? "node-click-flash" : ""}`}
              style={{
                animationDelay: `${NODE_BASE_MS + (i + 16) * NODE_STEP_MS}ms`,
                opacity: dim ? 0.22 : 1,
              }}
              onMouseEnter={() => setHovered(n.id)}
              onMouseLeave={() => setHovered((cur) => (cur === n.id ? null : cur))}
              onClick={() => flashAndRun(n.id, () => setOpen({ kind: "partner", id: f.id }))}
            >
              {isHovered && (
                <circle
                  cx={n.x}
                  cy={n.y}
                  r={n.r + 4}
                  fill="none"
                  stroke="var(--accent)"
                  strokeWidth={1.2}
                  strokeOpacity={0.7}
                />
              )}
              <circle
                cx={n.x}
                cy={n.y}
                r={n.r}
                fill={FOUNDER_AVATAR}
                stroke="var(--surface-0)"
                strokeWidth={2.5}
              />
              <text
                x={n.x}
                y={n.y + 3}
                textAnchor="middle"
                fontFamily="var(--font-display)"
                fontSize={Math.max(8.5, n.r * 0.7)}
                fontWeight={700}
                fill={INK_ON_LIGHT}
                style={{ pointerEvents: "none" }}
              >
                {initials(f.name)}
              </text>
              <NodeLabel
                x={n.x}
                y={n.y - n.r - 10}
                text={f.name}
                subtle={false}
                delay={LABEL_BASE_MS + (i + 8) * NODE_STEP_MS}
                hidden={!!dim}
              />
            </g>
          );
        })}
    </svg>
  );
}

function NodeLabel({
  x,
  y,
  text,
  subtle,
  delay = 0,
  hidden = false,
}: {
  x: number;
  y: number;
  text: string;
  subtle: boolean;
  delay?: number;
  hidden?: boolean;
}) {
  const fs = 10.5;
  const w = text.length * fs * 0.55 + 12;
  const h = fs + 8;
  return (
    <g
      className="graph-label"
      style={{
        animationDelay: `${delay}ms`,
        opacity: hidden ? 0 : 1,
        ["--label-opacity" as any]: hidden ? 0 : 1,
        transition: "opacity 200ms cubic-bezier(0.25, 1, 0.5, 1)",
      }}
    >
      <rect
        x={x - w / 2}
        y={y - h / 2}
        width={w}
        height={h}
        rx={4}
        fill="var(--surface-0)"
        fillOpacity={0.92}
        stroke="var(--line-faint)"
        strokeWidth={0.6}
      />
      <text
        x={x}
        y={y + fs * 0.35}
        textAnchor="middle"
        fontFamily="var(--font-body)"
        fontWeight={subtle ? 500 : 600}
        fontSize={fs}
        fill="var(--ink)"
      >
        {text}
      </text>
    </g>
  );
}

// ===========================================================================
// Layout
// ===========================================================================

function computeThemeGraph(activeFirms: Set<string>) {
  const liveThemeUsage: Record<ThemeKey, string[]> = {} as any;
  THEMES.forEach((t) => (liveThemeUsage[t.key] = []));
  PARTNERS.filter((p) => activeFirms.has(p.firm)).forEach((p) => {
    p.engages.forEach((k) => {
      if (liveThemeUsage[k]) liveThemeUsage[k].push(p.id);
    });
  });

  const liveThemes = THEMES.filter((t) => liveThemeUsage[t.key].length > 0);
  const livePartnerIds = new Set<string>();
  liveThemes.forEach((t) => liveThemeUsage[t.key].forEach((pid) => livePartnerIds.add(pid)));

  const nodes: Node[] = [];
  const links: Link[] = [];

  liveThemes.forEach((t) =>
    nodes.push({
      id: `T:${t.key}`,
      type: "theme",
      theme: t,
      r: 24 + liveThemeUsage[t.key].length * 4,
      x: 0,
      y: 0,
    })
  );

  Array.from(livePartnerIds).forEach((pid) => {
    nodes.push({ id: `P:${pid}`, type: "partner", pid, r: 12, x: 0, y: 0 });
    const p = partnerById(pid)!;
    p.engages.forEach((k) => {
      if (liveThemes.find((t) => t.key === k)) {
        links.push({ a: `P:${pid}`, b: `T:${k}`, len: 130 });
      }
    });
  });

  forceLayout(nodes, links, { W: SVG_W, H: SVG_H, charge: 5400, pad: 50, labelSpace: 30 });

  return { nodes, links };
}

function computeFollowerGraph(activeFirms: Set<string>) {
  const edges = FOLLOWS.filter((x) => {
    const pa = partnerById(x.partner);
    return pa && activeFirms.has(pa.firm);
  });

  const partnerIds = Array.from(new Set(edges.map((e) => e.partner)));
  const founderIds = Array.from(new Set(edges.map((e) => e.founder)));

  const deg: Record<string, number> = {};
  edges.forEach((e) => {
    deg[e.partner] = (deg[e.partner] || 0) + 1;
    deg[e.founder] = (deg[e.founder] || 0) + 1;
  });

  const nodes: Node[] = [];
  const links: Link[] = [];

  partnerIds.forEach((pid) =>
    nodes.push({ id: `P:${pid}`, type: "partner", pid, r: 11 + (deg[pid] || 1) * 1.6, x: 0, y: 0 })
  );
  founderIds.forEach((fid) =>
    nodes.push({ id: `F:${fid}`, type: "founder", fid, r: 12 + (deg[fid] || 1) * 2.4, x: 0, y: 0 })
  );

  edges.forEach((e) => links.push({ a: `P:${e.partner}`, b: `F:${e.founder}`, len: 150 }));

  forceLayout(nodes, links, { W: SVG_W, H: SVG_H, charge: 6200, pad: 60, labelSpace: 30 });

  return { nodes, links };
}

function forceLayout(
  nodes: Node[],
  links: Link[],
  opts: { W: number; H: number; charge?: number; pad?: number; labelSpace?: number }
) {
  const W = opts.W;
  const H = opts.H;
  const pad = opts.pad ?? 46;
  const charge = opts.charge ?? 5200;
  const labelSpace = opts.labelSpace ?? 20;

  // deterministic seed via simple hash of ids
  let seed = 1;
  for (const n of nodes) {
    for (let i = 0; i < n.id.length; i++) seed = (seed * 31 + n.id.charCodeAt(i)) >>> 0;
  }
  const rand = mulberry32(seed);

  nodes.forEach((n) => {
    n.x = W / 2 + (rand() - 0.5) * W * 0.6;
    n.y = H / 2 + (rand() - 0.5) * H * 0.6;
    (n as any).vx = 0;
    (n as any).vy = 0;
  });

  const byId: Record<string, Node> = {};
  nodes.forEach((n) => (byId[n.id] = n));

  const ITER = 320;
  for (let it = 0; it < ITER; it++) {
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i] as any;
        const b = nodes[j] as any;
        let dx = a.x - b.x;
        let dy = a.y - b.y;
        let d2 = dx * dx + dy * dy;
        if (d2 < 1) d2 = 1;
        const d = Math.sqrt(d2);
        const minGap = a.r + b.r + 34;
        const force = charge / d2;
        const ux = dx / d;
        const uy = dy / d;
        a.vx += ux * force;
        a.vy += uy * force;
        b.vx -= ux * force;
        b.vy -= uy * force;
        if (d < minGap) {
          const push = (minGap - d) / 2;
          a.vx += ux * push;
          a.vy += uy * push;
          b.vx -= ux * push;
          b.vy -= uy * push;
        }
      }
    }
    links.forEach((l) => {
      const a = byId[l.a] as any;
      const b = byId[l.b] as any;
      if (!a || !b) return;
      let dx = b.x - a.x;
      let dy = b.y - a.y;
      let d = Math.sqrt(dx * dx + dy * dy) || 1;
      const target = l.len || 150;
      const k = (d - target) * 0.045;
      const ux = dx / d;
      const uy = dy / d;
      a.vx += ux * k;
      a.vy += uy * k;
      b.vx -= ux * k;
      b.vy -= uy * k;
    });
    nodes.forEach((n) => {
      const m = n as any;
      m.vx += (W / 2 - m.x) * 0.0016;
      m.vy += (H / 2 - m.y) * 0.0016;
      m.x += Math.max(-14, Math.min(14, m.vx)) * 0.5;
      m.y += Math.max(-14, Math.min(14, m.vy)) * 0.5;
      m.vx *= 0.86;
      m.vy *= 0.86;
    });
  }

  nodes.forEach((n) => {
    const top = n.r + labelSpace;
    n.x = Math.max(pad + n.r, Math.min(W - pad - n.r, n.x));
    n.y = Math.max(pad + top, Math.min(H - pad - n.r - 8, n.y));
  });
}

function mulberry32(a: number) {
  return function () {
    let t = (a += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
