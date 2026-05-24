"use client";

import { initials } from "@/lib/data";
import { INK_ON_LIGHT } from "@/lib/ui";

type Size = "xs" | "sm" | "md" | "lg" | "xl";

const sizeMap: Record<Size, { dim: string; text: string }> = {
  xs: { dim: "h-5 w-5", text: "text-[9px]" },
  sm: { dim: "h-7 w-7", text: "text-meta" },
  md: { dim: "h-9 w-9", text: "text-caption" },
  lg: { dim: "h-12 w-12", text: "text-body" },
  xl: { dim: "h-16 w-16", text: "text-h-md" },
};

type Props = {
  name: string;
  color: string;
  size?: Size;
  textColor?: string;
  className?: string;
  watched?: boolean;
};

export function Avatar({ name, color, size = "md", textColor, className = "", watched }: Props) {
  const cfg = sizeMap[size];
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center rounded-full font-display font-bold ${cfg.dim} ${cfg.text} ${className}`}
      style={{
        background: color,
        color: textColor ?? INK_ON_LIGHT,
        letterSpacing: "-0.01em",
        boxShadow: watched
          ? "0 0 0 2px var(--surface-1), 0 0 0 3.5px var(--accent)"
          : undefined,
      }}
      aria-hidden
    >
      {initials(name)}
    </span>
  );
}
