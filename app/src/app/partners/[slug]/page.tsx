import Link from "next/link";
import { notFound } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { loadFirmGraph, slugify } from "@/lib/data";

type PageProps = { params: Promise<{ slug: string }> };

export default async function PartnerPage({ params }: PageProps) {
  const { slug } = await params;
  const graph = await loadFirmGraph();
  const partner = graph?.partners.find((p) => slugify(p.name) === slug);

  if (!partner) {
    notFound();
  }

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <div className="font-mono text-xs uppercase tracking-widest text-zinc-500">
          Partner
          <span className="px-2 text-zinc-300">·</span>
          {partner.firm}
        </div>
        <div className="flex items-baseline justify-between">
          <h1 className="text-3xl font-semibold tracking-tight">{partner.name}</h1>
          <div className="font-mono text-xs uppercase text-zinc-500">{partner.role}</div>
        </div>
      </header>

      <Separator />

      <section className="grid gap-4 md:grid-cols-3">
        <MetricSlot label="Followers" value="—" delta="—" />
        <MetricSlot label="Posts / 30d" value="—" delta="—" />
        <MetricSlot label="Following added / 30d" value="—" delta="—" />
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm uppercase tracking-widest text-zinc-500">
              Recent posts
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-zinc-500">
            Wired by the frontend workspace from <code>data/social/{partner.x_handle}.json</code>.
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm uppercase tracking-widest text-zinc-500">
              Active themes
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-1.5 text-sm text-zinc-500">
            <Badge variant="outline" className="font-mono text-[10px]">tbd</Badge>
            <Badge variant="outline" className="font-mono text-[10px]">tbd</Badge>
            <Badge variant="outline" className="font-mono text-[10px]">tbd</Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm uppercase tracking-widest text-zinc-500">
              Engagement-revealed interests
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-zinc-500">
            Likes and replies are typically more predictive than posts. Awaits Phase 4.
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm uppercase tracking-widest text-zinc-500">
              External links
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 font-mono text-xs">
            {partner.x_handle && (
              <Link
                className="block text-zinc-600 hover:underline dark:text-zinc-300"
                href={`https://x.com/${partner.x_handle}`}
              >
                x.com/{partner.x_handle}
              </Link>
            )}
            {partner.linkedin_url && (
              <Link
                className="block text-zinc-600 hover:underline dark:text-zinc-300"
                href={partner.linkedin_url}
              >
                linkedin
              </Link>
            )}
            {partner.blog_url && (
              <Link
                className="block text-zinc-600 hover:underline dark:text-zinc-300"
                href={partner.blog_url}
              >
                blog
              </Link>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function MetricSlot({ label, value, delta }: { label: string; value: string; delta: string }) {
  return (
    <div className="rounded-md border border-zinc-200 p-4 dark:border-zinc-800">
      <div className="font-mono text-[10px] uppercase tracking-widest text-zinc-500">{label}</div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="font-mono text-2xl tabular-nums">{value}</span>
        <span className="font-mono text-xs tabular-nums text-zinc-500">Δ {delta}</span>
      </div>
    </div>
  );
}
