import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "deal_flow",
  description: "Deal-flow finder",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
