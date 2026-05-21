import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { loadDigest } from "@/lib/data";

function formatScore(score: number) {
  return `${Math.round(score * 100)}`;
}

export default async function Home() {
  const digest = await loadDigest();

  if (!digest) {
    return (
      <div className="rounded-md border border-dashed border-zinc-300 p-10 text-center text-zinc-500 dark:border-zinc-700">
        No digest yet. Run <code className="font-mono">python -m pipeline.main run --phase 1</code>
        {" "}then continue through phase 3.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <section className="space-y-1">
        <div className="font-mono text-xs uppercase tracking-widest text-zinc-500">
          Daily digest · generated{" "}
          <span className="text-zinc-900 dark:text-zinc-100">{digest.generated_at}</span>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">
          {digest.cards.length} signal{digest.cards.length === 1 ? "" : "s"} surfaced
        </h1>
        <p className="max-w-2xl text-sm text-zinc-600 dark:text-zinc-400">
          Discovery, not catch-up. Every metric below is a delta against the prior period.
          Confidence is a calibrated 0–100 score.
        </p>
      </section>

      <Separator />

      <section className="grid gap-4 md:grid-cols-2">
        {digest.cards.map((card) => (
          <Card key={card.signal.id}>
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <Badge variant="secondary" className="font-mono text-[10px] uppercase">
                    {card.signal.kind.replaceAll("_", " ")}
                  </Badge>
                  <CardTitle className="text-base leading-snug">{card.headline}</CardTitle>
                </div>
                <div className="text-right">
                  <div className="font-mono text-2xl tabular-nums text-zinc-900 dark:text-zinc-100">
                    {formatScore(card.signal.score)}
                  </div>
                  <div className="font-mono text-[10px] uppercase tracking-widest text-zinc-400">
                    confidence
                  </div>
                </div>
              </div>
              <CardDescription className="pt-2">{card.one_liner}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-wrap gap-1.5">
                {card.evidence_chips.map((chip) => (
                  <span
                    key={chip}
                    className="rounded border border-zinc-200 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wide text-zinc-600 dark:border-zinc-800 dark:text-zinc-300"
                  >
                    {chip}
                  </span>
                ))}
              </div>
              <a
                href={card.drill_down_url}
                className="font-mono text-xs text-zinc-500 underline-offset-2 hover:underline"
                target="_blank"
                rel="noreferrer"
              >
                drill down ↗
              </a>
            </CardContent>
          </Card>
        ))}
      </section>
    </div>
  );
}
