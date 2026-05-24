"use client";

import { FirmFilter } from "./FirmFilter";

type Props = {
  eyebrow: string;
  title?: React.ReactNode;
  description?: string;
  showFirmFilter?: boolean;
  /** Optional masthead-right line, e.g. "Daily digest · 25 May 2026". */
  dateline?: string;
};

export function PageHeader({
  eyebrow,
  title,
  description,
  showFirmFilter = true,
  dateline,
}: Props) {
  return (
    <header className="mb-9 border-b border-line-faint pb-7">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2 stagger-in stagger-1">
        <span className="eyebrow">{eyebrow}</span>
        {dateline && <span className="t-mono-cap">{dateline}</span>}
      </div>

      {title && (
        <h1 className="mt-5 font-display text-h-2xl font-bold text-ink max-w-[18ch] stagger-in stagger-2">
          {title}
        </h1>
      )}

      {description && (
        <p className={`t-lead stagger-in stagger-3 ${title ? "mt-5" : "mt-3"}`}>{description}</p>
      )}

      {showFirmFilter && (
        <div className="stagger-in stagger-4">
          <FirmFilter />
        </div>
      )}
    </header>
  );
}
