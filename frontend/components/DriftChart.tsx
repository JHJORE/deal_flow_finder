"use client";

import { PERIODS, THEMES, themeColor } from "@/lib/data";
import { useRadar } from "@/lib/state";
import { useEffect, useMemo, useState } from "react";
import type { Theme } from "@/lib/types";

const PAD = { l: 36, r: 18, t: 12, b: 28 };
const LINE_LEN = 900; // approximate path length; dashoffset starts here, animates to 0

export function DriftChart() {
  const { setSelectedTheme, selectedTheme } = useRadar();
  const [hover, setHover] = useState<{ i: number; t: Theme } | null>(null);
  const [drawn, setDrawn] = useState(false);

  // animate the lines in on first mount only — subsequent prop changes don't replay
  useEffect(() => {
    const id = requestAnimationFrame(() => setDrawn(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const W = 720;
  const H = 320;
  const innerW = W - PAD.l - PAD.r;
  const innerH = H - PAD.t - PAD.b;

  const max = useMemo(() => Math.max(...THEMES.flatMap((t) => t.share)), []);
  const yTicks = useMemo(() => niceTicks(max, 4), [max]);

  function pointPath(theme: Theme) {
    return theme.share
      .map((v, i) => {
        const x = PAD.l + (i / (PERIODS.length - 1)) * innerW;
        const y = PAD.t + (1 - v / max) * innerH;
        return `${i === 0 ? "M" : "L"}${x.toFixed(2)} ${y.toFixed(2)}`;
      })
      .join(" ");
  }

  return (
    <div className="relative">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="block w-full h-[320px]"
        role="img"
        aria-label="Theme drift over time"
      >
        {/* horizontal grid */}
        {yTicks.map((t, i) => {
          const y = PAD.t + (1 - t / max) * innerH;
          return (
            <g key={i}>
              <line
                x1={PAD.l}
                x2={W - PAD.r}
                y1={y}
                y2={y}
                stroke="var(--line-faint)"
                strokeDasharray="3 4"
                strokeWidth="0.5"
              />
              <text
                x={PAD.l - 8}
                y={y + 3}
                textAnchor="end"
                fontFamily="var(--font-mono)"
                fontSize="10"
                fill="var(--ink-4)"
              >
                {t}%
              </text>
            </g>
          );
        })}

        {/* period ticks */}
        {PERIODS.map((p, i) => {
          const x = PAD.l + (i / (PERIODS.length - 1)) * innerW;
          return (
            <text
              key={p}
              x={x}
              y={H - PAD.b + 18}
              textAnchor="middle"
              fontFamily="var(--font-mono)"
              fontSize="10"
              fill="var(--ink-4)"
            >
              {p}
            </text>
          );
        })}

        {THEMES.map((theme, idx) => {
          const isSelected = theme.key === selectedTheme;
          // cooling theme keeps its dashed pattern; the rest draw in on mount
          const baseDash = theme.trend === "cooling" ? "5 5" : "";
          return (
            <g key={theme.key}>
              <path
                d={pointPath(theme)}
                stroke={themeColor(theme)}
                strokeOpacity={isSelected ? 1 : 0.55}
                strokeWidth={isSelected ? 2.3 : 1.4}
                strokeDasharray={baseDash || LINE_LEN}
                strokeDashoffset={baseDash ? 0 : drawn ? 0 : LINE_LEN}
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                className={`cursor-pointer ${baseDash ? "" : "line-draw"}`}
                style={{ transitionDelay: `${idx * 90}ms` }}
                onClick={() => setSelectedTheme(theme.key)}
              />
              {theme.share.map((v, i) => {
                const x = PAD.l + (i / (PERIODS.length - 1)) * innerW;
                const y = PAD.t + (1 - v / max) * innerH;
                return (
                  <circle
                    key={i}
                    cx={x}
                    cy={y}
                    r={isSelected ? 3.2 : 2.4}
                    fill={themeColor(theme)}
                    fillOpacity={isSelected ? 1 : 0.7}
                    className="cursor-pointer"
                    onClick={() => setSelectedTheme(theme.key)}
                    onMouseEnter={() => setHover({ i, t: theme })}
                    onMouseLeave={() => setHover(null)}
                  />
                );
              })}
              {/* end-of-line label */}
              <text
                x={PAD.l + innerW + 6}
                y={PAD.t + (1 - theme.share[theme.share.length - 1] / max) * innerH + 3}
                fontFamily="var(--font-body)"
                fontSize="10.5"
                fontWeight={isSelected ? 700 : 500}
                fill={themeColor(theme)}
                opacity={isSelected ? 1 : 0.55}
                style={{ display: "none" }}
              >
                {theme.label}
              </text>
            </g>
          );
        })}
      </svg>

      {hover && (
        <div
          className="pointer-events-none absolute rounded-md border border-line bg-surface-3 px-3 py-2 shadow-2xl"
          style={{
            left: `${(PAD.l + (hover.i / (PERIODS.length - 1)) * innerW) / W * 100}%`,
            top: 4,
            transform: "translateX(-50%)",
          }}
        >
          <div className="eyebrow" style={{ color: themeColor(hover.t) }}>
            {hover.t.label}
          </div>
          <div className="mt-1 t-h-sm tabnum text-ink">
            {hover.t.share[hover.i]}%{" "}
            <span className="text-meta font-normal text-ink-4">mention share</span>
          </div>
          <div className="font-mono text-meta tabnum text-ink-4">{PERIODS[hover.i]}</div>
        </div>
      )}
    </div>
  );
}

function niceTicks(max: number, n: number) {
  const step = niceStep(max / n);
  const ticks: number[] = [];
  for (let v = 0; v <= max; v += step) ticks.push(v);
  return ticks;
}

function niceStep(raw: number) {
  if (raw <= 0) return 1;
  const pow = Math.pow(10, Math.floor(Math.log10(raw)));
  const norm = raw / pow;
  if (norm < 1.5) return 1 * pow;
  if (norm < 3) return 2 * pow;
  if (norm < 7) return 5 * pow;
  return 10 * pow;
}
