type Props = { size?: number; className?: string };

// The product's signature mark. A clean radar dial: two rings, faint
// crosshairs, ember center dot. Rendered as inline SVG so it inherits
// `color` from `currentColor` and scales crisply at any density.
export function RadarMark({ size = 22, className = "" }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      className={className}
      aria-hidden
      role="presentation"
    >
      <circle
        cx="12"
        cy="12"
        r="11"
        fill="none"
        stroke="currentColor"
        strokeWidth="0.7"
        strokeOpacity="0.55"
      />
      <circle
        cx="12"
        cy="12"
        r="6.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="0.7"
        strokeOpacity="0.32"
      />
      <line
        x1="0.6"
        y1="12"
        x2="23.4"
        y2="12"
        stroke="currentColor"
        strokeWidth="0.4"
        strokeOpacity="0.2"
      />
      <line
        x1="12"
        y1="0.6"
        x2="12"
        y2="23.4"
        stroke="currentColor"
        strokeWidth="0.4"
        strokeOpacity="0.2"
      />
      <circle cx="12" cy="12" r="2.2" fill="currentColor" />
    </svg>
  );
}
