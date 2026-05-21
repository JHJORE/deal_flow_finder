import Link from "next/link";
import { notFound } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { loadFirmGraph, slugify } from "@/lib/data";

type PageProps = { params: Promise<{ slug: string }> };

export default async function CompanyPage({ params }: PageProps) {
  const { slug } = await params;
  const graph = await loadFirmGraph();
  const company = graph?.companies.find((c) => slugify(c.name) === slug);

  if (!company) {
    notFound();
  }

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <div className="font-mono text-xs uppercase tracking-widest text-zinc-500">
          Company
          <span className="px-2 text-zinc-300">·</span>
          {company.stage.replaceAll("_", " ")}
        </div>
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="text-3xl font-semibold tracking-tight">{company.name}</h1>
          <div className="flex gap-1.5">
            {company.invested_by.map((firm) => (
              <Badge key={firm} variant="secondary" className="font-mono text-[10px] uppercase">
                {firm}
              </Badge>
            ))}
          </div>
        </div>
      </header>

      <Separator />

      <section className="grid gap-4 md:grid-cols-3">
        <MetricSlot label="LinkedIn headcount" value="—" delta="—" />
        <MetricSlot label="Senior hires / 30d" value="—" delta="—" />
        <MetricSlot label="Recent Form D" value="—" delta="—" />
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm uppercase tracking-widest text-zinc-500">
              About
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-zinc-600 dark:text-zinc-300">
            {company.description || "—"}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm uppercase tracking-widest text-zinc-500">
              External links
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 font-mono text-xs">
            {company.website && (
              <Link className="block hover:underline" href={company.website}>
                {company.website}
              </Link>
            )}
            {company.linkedin_company_url && (
              <Link className="block hover:underline" href={company.linkedin_company_url}>
                linkedin
              </Link>
            )}
          </CardContent>
        </Card>
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm uppercase tracking-widest text-zinc-500">
              Recent senior hires
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-zinc-500">
            Slot wired by the frontend workspace from{" "}
            <code>data/linkedin/&lt;company-slug&gt;.json</code>. First senior hire (CFO, GC, VP
            Sales) is the Tier-2 founder-heat signal.
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
