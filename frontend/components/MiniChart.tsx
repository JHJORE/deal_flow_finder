"use client";

import { PERIODS } from "@/lib/data";

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
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="absolute inset-0 h-full w-full">
        {yTicks.map((t, i) => (
          <line
            key={i}
            x1="0"
            x2={W}
            y1={H - (t / max) * (H - 14) - 4}
            y2={H - (t / max) * (H - 14) - 4}
            stroke="var(--line-faint)"
            strokeWidth="0.18"
            strokeDasharray="0.6 0.8"
          />
        ))}
        {data.map((v, i) => {
          const x = i * (W / data.length) + 0.6;
          const h = (v / max) * (H - 14);
          const y = H - h - 4;
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
      {/* y-axis labels overlay */}
      <div className="pointer-events-none absolute inset-0">
        {yTicks.map((t, i) => {
          const top = (1 - t / max) * (height - 28) + 4;
          return (
            <span
              key={i}
              className="absolute -translate-y-1/2 font-mono text-[9.5px] tabnum text-ink-4"
              style={{ left: 0, top }}
            >
              {t}
            </span>
          );
        })}
      </div>
      <div className="pointer-events-none absolute bottom-0 left-0 right-0 flex justify-between px-1 font-mono text-[10px] tabnum text-ink-4">
        {PERIODS.map((p) => (
          <span key={p}>{p}</span>
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
  const top = 6;
  const bottom = H - 8;
  const usable = bottom - top;

  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * W;
    const y = bottom - (v / max) * usable;
    return { x, y };
  });

  const linePath = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(" ");
  const areaPath = `${linePath} L${pts[pts.length - 1].x} ${bottom} L${pts[0].x} ${bottom} Z`;

  const yTicks = niceTicks(max, 3);

  return (
    <div className="relative" style={{ height }}>
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="absolute inset-0 h-full w-full">
        {yTicks.map((t, i) => (
          <line
            key={i}
            x1="0"
            x2={W}
            y1={bottom - (t / max) * usable}
            y2={bottom - (t / max) * usable}
            stroke="var(--line-faint)"
            strokeWidth="0.18"
            strokeDasharray="0.6 0.8"
          />
        ))}
        {fill && (
          <path d={areaPath} fill={accent} fillOpacity="0.1" />
        )}
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
      <div className="pointer-events-none absolute inset-0">
        {yTicks.map((t, i) => {
          const y = bottom - (t / max) * usable;
          const topPx = (y / H) * height;
          return (
            <span
              key={i}
              className="absolute -translate-y-1/2 font-mono text-[9.5px] tabnum text-ink-4"
              style={{ left: 0, top: topPx }}
            >
              {t}
            </span>
          );
        })}
      </div>
      <div className="pointer-events-none absolute bottom-0 left-0 right-0 flex justify-between px-1 font-mono text-[10px] tabnum text-ink-4">
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
