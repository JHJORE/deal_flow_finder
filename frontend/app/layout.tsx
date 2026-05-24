import type { Metadata, Viewport } from "next";
import { Bricolage_Grotesque, Hanken_Grotesk, Fragment_Mono } from "next/font/google";
import "./globals.css";

const display = Bricolage_Grotesque({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-display",
  display: "swap",
});

const body = Hanken_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
  display: "swap",
});

const mono = Fragment_Mono({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Dealflow Radar — pre-deal signal intelligence",
  description:
    "Pre-deal signal intelligence for early-stage venture. Surfaces convergence, founder warm-ups, and quiet Form D filings before the market notices.",
};

// matches --surface-0 — so the browser chrome (mobile address bar, etc.)
// blends into the page surface rather than reverting to system grey
export const viewport: Viewport = {
  themeColor: "#171513",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} ${mono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
