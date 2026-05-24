// Named UI constants for color values that appear in JS-driven props
// (Avatar fills, chart accents, etc.) where Tailwind class lookup isn't
// available. Anything in CSS (className) should still use tokens.

/** Light ink on coloured avatars (sequoia / a16z / yc). */
export const INK_ON_DARK = "oklch(96% 0.005 60)";

/** Dark ink on light avatars (founder / neutral). */
export const INK_ON_LIGHT = "oklch(15% 0.008 60)";

/** Standard founder / neutral avatar background — a warm off-white. */
export const FOUNDER_AVATAR = "oklch(94% 0.008 75)";

/** Mid-saturation accent used by chart curves whose data isn't yet wired
 * to a real theme/firm (e.g. founder profile line chart). */
export const ACCENT_RAW = "oklch(72% 0.155 50)";

/** Faint grid lines inside SVG charts where Tailwind classes don't reach. */
export const CHART_GRID = "var(--line-faint)";

/** Bar baseline for inactive periods (the first 3 columns in the mini bar
 * charts on profile views). */
export const CHART_BAR_BASE = "var(--line-hard)";
