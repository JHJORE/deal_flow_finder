import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          0: "var(--surface-0)",
          1: "var(--surface-1)",
          2: "var(--surface-2)",
          3: "var(--surface-3)",
          raised: "var(--surface-raised)",
        },
        line: {
          DEFAULT: "var(--line)",
          faint: "var(--line-faint)",
          hard: "var(--line-hard)",
        },
        ink: {
          DEFAULT: "var(--ink)",
          2: "var(--ink-2)",
          3: "var(--ink-3)",
          4: "var(--ink-4)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          deep: "var(--accent-deep)",
          soft: "var(--accent-soft)",
          faint: "var(--accent-faint)",
        },
        positive: "var(--positive)",
        "positive-soft": "var(--positive-soft)",
        caution: "var(--caution)",
        negative: "var(--negative)",
        "negative-soft": "var(--negative-soft)",
        info: "var(--info)",
        firm: {
          sequoia: "var(--firm-sequoia)",
          a16z: "var(--firm-a16z)",
          yc: "var(--firm-yc)",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "ui-sans-serif", "system-ui"],
        body: ["var(--font-body)", "ui-sans-serif", "system-ui"],
        mono: ["var(--font-mono)", "ui-monospace"],
      },
      fontSize: {
        // semantic prose scale
        "eyebrow": ["0.6875rem", { lineHeight: "1.4", letterSpacing: "0.14em" }],
        "meta": ["0.75rem", { lineHeight: "1.45" }],
        "caption": ["0.8125rem", { lineHeight: "1.55" }],
        "body": ["0.9375rem", { lineHeight: "1.65" }],
        "lead": ["1rem", { lineHeight: "1.6" }],
        // display scale
        "h-sm": ["1rem", { lineHeight: "1.3", letterSpacing: "-0.008em" }],
        "h-md": ["1.1875rem", { lineHeight: "1.25", letterSpacing: "-0.018em" }],
        "h-lg": ["1.5rem", { lineHeight: "1.2", letterSpacing: "-0.018em" }],
        "h-xl": ["2.125rem", { lineHeight: "1.1", letterSpacing: "-0.028em" }],
        // h-2xl is fluid — page-level mastheads get genuine editorial scale on wider viewports
        "h-2xl": [
          "clamp(2.25rem, 1.4rem + 3.2vw, 4.25rem)",
          { lineHeight: "1.0", letterSpacing: "-0.038em" },
        ],
        // h-3xl is reserved for the single biggest moment in the app — the Filing dossier issuer
        "h-3xl": [
          "clamp(2.75rem, 1.6rem + 4.6vw, 5.5rem)",
          { lineHeight: "0.97", letterSpacing: "-0.042em" },
        ],
        // numeric scale
        "num-sm": ["1.125rem", { lineHeight: "1", letterSpacing: "-0.015em" }],
        "num-md": ["1.5rem", { lineHeight: "1", letterSpacing: "-0.02em" }],
        "num-lg": ["2rem", { lineHeight: "1", letterSpacing: "-0.025em" }],
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "6px",
        md: "10px",
        lg: "14px",
        xl: "18px",
      },
      letterSpacing: {
        editorial: "-0.025em",
        "editorial-tight": "-0.035em",
      },
    },
  },
  plugins: [],
};

export default config;
