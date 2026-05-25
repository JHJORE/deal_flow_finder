"use client";

import { COMPANIES, FIRMS, PARTNERS, firmColor } from "@/lib/data";
import { useRadar } from "@/lib/state";
import type { FirmId } from "@/lib/types";

export function FirmFilter() {
  const { activeFirms, toggleFirm, view } = useRadar();
  const order: FirmId[] = ["sequoia", "a16z", "yc"];
  const countFor = (id: FirmId) =>
    view === "portfolio"
      ? COMPANIES.filter((c) => c.firm === id).length
      : PARTNERS.filter((p) => p.firm === id).length;

  return (
    <div className="mt-5 flex flex-wrap items-center gap-2">
      <span className="eyebrow mr-2">Firms</span>
      {order.map((id) => {
        const f = FIRMS[id];
        const isOn = activeFirms.has(id);
        const count = countFor(id);
        return (
          <button
            key={id}
            onClick={() => toggleFirm(id)}
            className={`group inline-flex items-center gap-2 rounded-full border px-3 py-1 text-meta font-medium transition-colors ${
              isOn
                ? "border-line-hard bg-surface-2 text-ink"
                : "border-line-faint text-ink-3 hover:border-line-hard hover:text-ink"
            }`}
          >
            <span
              className="h-1.5 w-1.5 rounded-full"
              style={{ background: firmColor(id), opacity: isOn ? 1 : 0.45 }}
              aria-hidden
            />
            <span>{f.name}</span>
            <span className="font-mono text-eyebrow tabnum text-ink-4">{count}</span>
          </button>
        );
      })}
    </div>
  );
}
