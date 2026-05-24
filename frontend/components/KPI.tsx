"use client";

import { useEffect, useRef, useState } from "react";

type Tone = "default" | "up" | "warn" | "down";

export function KPIGrid({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-1 gap-px overflow-hidden rounded-lg border border-line-faint bg-line-faint sm:grid-cols-2 lg:grid-cols-4">
      {children}
    </div>
  );
}

type Props = {
  label: string;
  value: React.ReactNode;
  hint: string;
  tone?: Tone;
};

const toneClass: Record<Tone, string> = {
  default: "text-ink-3",
  up: "text-positive",
  warn: "text-accent",
  down: "text-negative",
};

export function KPI({ label, value, hint, tone = "default" }: Props) {
  // count up only on first mount, then settle to the live value
  const isNumeric = typeof value === "number";
  const animated = useCountUp(isNumeric ? (value as number) : 0, 680);
  const display = isNumeric ? animated : value;

  return (
    <div className="relative flex flex-col gap-2 bg-surface-1 px-5 py-5">
      <span className="eyebrow">{label}</span>
      <span className="n-lg text-ink">{display}</span>
      <span className={`text-meta ${toneClass[tone]}`}>{hint}</span>
    </div>
  );
}

// ease-out-quart, runs once per target, respects reduced motion
function useCountUp(target: number, duration = 600) {
  const [value, setValue] = useState(target);
  const firstRender = useRef(true);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setValue(target);
      return;
    }
    if (target === 0) {
      setValue(0);
      return;
    }
    // only animate on first mount; later updates jump instantly
    if (!firstRender.current) {
      setValue(target);
      return;
    }
    firstRender.current = false;

    const start = performance.now();
    let raf = 0;
    const tick = (now: number) => {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 4);
      setValue(Math.round(target * eased));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);

  return value;
}
