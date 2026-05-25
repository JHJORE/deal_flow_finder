"use client";

import { useEffect, useRef, useState } from "react";

const EASE = "cubic-bezier(0.16, 1, 0.3, 1)";

export function LoginPill() {
  const [revealed, setRevealed] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, []);

  function onClick() {
    setRevealed(true);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => setRevealed(false), 2600);
  }

  return (
    <button
      type="button"
      onClick={onClick}
      aria-live="polite"
      aria-label={revealed ? "Login — coming soon" : "Login"}
      className="group fixed right-6 top-5 z-40 inline-flex items-center gap-2.5 rounded-full border border-line bg-surface-2/90 px-3.5 py-[7px] backdrop-blur-md transition-colors duration-300 hover:border-line-hard hover:bg-surface-3"
    >
      <span
        aria-hidden
        className={`h-[5px] w-[5px] rounded-full transition-colors duration-500 ${
          revealed ? "bg-accent" : "bg-ink-3 group-hover:bg-accent"
        }`}
      />
      <span className="relative inline-grid items-center">
        <span
          aria-hidden
          className="col-start-1 row-start-1 eyebrow !text-ink-2 group-hover:!text-ink whitespace-nowrap transition-all"
          style={{
            transitionDuration: "360ms",
            transitionTimingFunction: EASE,
            transform: revealed ? "translateY(-6px)" : "translateY(0)",
            opacity: revealed ? 0 : 1,
            color: revealed ? "transparent" : undefined,
          }}
        >
          Login
        </span>
        <span
          aria-hidden
          className="col-start-1 row-start-1 eyebrow whitespace-nowrap transition-all"
          style={{
            transitionDuration: "360ms",
            transitionTimingFunction: EASE,
            transform: revealed ? "translateY(0)" : "translateY(6px)",
            opacity: revealed ? 1 : 0,
            color: "var(--accent)",
          }}
        >
          Coming soon
        </span>
      </span>
    </button>
  );
}
