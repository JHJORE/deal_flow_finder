import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LAUNCH — Deal Flow",
  description: "Leading-indicator signals for early-stage VC.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-zinc-50 text-zinc-900 dark:bg-black dark:text-zinc-100">
        <header className="border-b border-zinc-200 dark:border-zinc-800">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
            <Link href="/" className="font-mono text-sm tracking-tight">
              LAUNCH<span className="text-zinc-400"> /</span> deal flow
            </Link>
            <nav className="flex gap-6 text-xs uppercase tracking-widest text-zinc-500">
              <Link href="/" className="hover:text-zinc-900 dark:hover:text-zinc-100">
                Digest
              </Link>
              <Link
                href="/partners/roelof-botha"
                className="hover:text-zinc-900 dark:hover:text-zinc-100"
              >
                Partners
              </Link>
              <Link
                href="/companies/stripe"
                className="hover:text-zinc-900 dark:hover:text-zinc-100"
              >
                Companies
              </Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-10">{children}</main>
        <footer className="border-t border-zinc-200 dark:border-zinc-800">
          <div className="mx-auto max-w-6xl px-6 py-4 font-mono text-xs text-zinc-400">
            LAUNCH · discovery before consensus
          </div>
        </footer>
      </body>
    </html>
  );
}
