"use client";

import { PERIODS } from "@/lib/data";

// reserved px strips around the SVG body for axis labels.
// kept in sync between Bar/Line so they stack identically inside a Panel.
const PAD_L = 28;
const PAD_B = 18;

type BarProps = {
  data: number[];
  highlightFrom?: number;
  accent: string;
  base?: string;
  height?: number;
};

export function MiniBarChart({
  data,
  highlightFrom = 3,
  accent,
  base = "var(--line-hard)",
  height = 200,
}: BarProps) {
  if (data.length === 0) return null;
  const max = Math.max(...data, 1);
  const W = 100;
  const H = 100;
  const barW = W / data.length - 1.2;
  const yTicks = niceTicks(max, 3);

  return (
    <div className="relative" style={{ height }}>
      {/* y-axis labels — sit in the left strip, right-aligned against the chart */}
      <div
        className="pointer-events-none absolute left-0 top-0"
        style={{ width: PAD_L, bottom: PAD_B }}
      >
        {yTicks.map((t) => (
          <span
            key={t}
            className="absolute right-1.5 -translate-y-1/2 font-mono text-[9.5px] tabnum text-ink-4"
            style={{ top: `${(1 - t / max) * 100}%` }}
          >
            {t}
          </span>
        ))}
      </div>

      {/* chart body — inset by the label strips */}
      <div
        className="absolute right-0 top-0"
        style={{ left: PAD_L, bottom: PAD_B }}
      >
        <svg
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="none"
          className="block h-full w-full"
        >
          {yTicks.map((t) => {
            const y = (1 - t / max) * H;
            return (
              <line
                key={t}
                x1="0"
                x2={W}
                y1={y}
                y2={y}
                stroke="var(--line-faint)"
                strokeWidth="0.18"
                strokeDasharray="0.6 0.8"
              />
            );
          })}
          {data.map((v, i) => {
            const x = i * (W / data.length) + 0.6;
            const h = (v / max) * H;
            const y = H - h;
            const fill = i >= highlightFrom ? accent : base;
            return (
              <rect
                key={i}
                x={x}
                y={y}
                width={barW}
                height={h}
                fill={fill}
                rx="0.6"
              />
            );
          })}
        </svg>
      </div>

      {/* x-axis labels — centered under each bar in the bottom strip */}
      <div
        className="pointer-events-none absolute right-0 bottom-0"
        style={{ left: PAD_L, height: PAD_B }}
      >
        {PERIODS.map((p, i) => (
          <span
            key={p}
            className="absolute bottom-0 -translate-x-1/2 font-mono text-[10px] tabnum text-ink-4"
            style={{ left: `${((i + 0.5) / PERIODS.length) * 100}%` }}
          >
            {p}
          </span>
        ))}
      </div>
    </div>
  );
}

type LineProps = {
  data: number[];
  accent: string;
  height?: number;
  fill?: boolean;
};

export function MiniLineChart({
  data,
  accent,
  height = 200,
  fill = true,
}: LineProps) {
  if (data.length === 0) return null;
  const max = Math.max(...data, 1);
  const W = 100;
  const H = 100;

  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * W;
    const y = H - (v / max) * H;
    return { x, y };
  });

  const linePath = pts
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(2)} ${p.y.toFixed(2)}`)
    .join(" ");
  const areaPath = `${linePath} L${pts[pts.length - 1].x} ${H} L${pts[0].x} ${H} Z`;

  const yTicks = niceTicks(max, 3);

  return (
    <div className="relative" style={{ height }}>
      {/* y-axis labels — same strip as MiniBarChart for vertical alignment when stacked */}
      <div
        className="pointer-events-none absolute left-0 top-0"
        style={{ width: PAD_L, bottom: PAD_B }}
      >
        {yTicks.map((t) => (
          <span
            key={t}
            className="absolute right-1.5 -translate-y-1/2 font-mono text-[9.5px] tabnum text-ink-4"
            style={{ top: `${(1 - t / max) * 100}%` }}
          >
            {t}
          </span>
        ))}
      </div>

      {/* chart body */}
      <div
        className="absolute right-0 top-0"
        style={{ left: PAD_L, bottom: PAD_B }}
      >
        <svg
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="none"
          className="block h-full w-full"
        >
          {yTicks.map((t) => {
            const y = H - (t / max) * H;
            return (
              <line
                key={t}
                x1="0"
                x2={W}
                y1={y}
                y2={y}
                stroke="var(--line-faint)"
                strokeWidth="0.18"
                strokeDasharray="0.6 0.8"
              />
            );
          })}
          {fill && <path d={areaPath} fill={accent} fillOpacity="0.1" />}
          <path
            d={linePath}
            fill="none"
            stroke={accent}
            strokeWidth="0.7"
            strokeLinecap="round"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />
          {pts.map((p, i) => (
            <circle key={i} cx={p.x} cy={p.y} r="0.7" fill={accent} />
          ))}
        </svg>
      </div>

      {/* x-axis labels — first/last pinned to body edges so they sit under the endpoint dots */}
      <div
        className="pointer-events-none absolute right-0 bottom-0 flex justify-between font-mono text-[10px] tabnum text-ink-4"
        style={{ left: PAD_L, height: PAD_B }}
      >
        {PERIODS.map((p) => (
          <span key={p}>{p}</span>
        ))}
      </div>
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
