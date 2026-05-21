import fs from "node:fs/promises";
import path from "node:path";

// Frontend reads sample fixtures from the repo's data/ directory. Once the
// FastAPI server is wired up, swap these helpers for fetch() calls against
// http://localhost:8000/{digest,firm-graph,filings}. The shape is identical
// — the Python serialisation helpers in pipeline/main.py match these types.

const DATA_ROOT = path.resolve(process.cwd(), "..", "data");

async function readJson<T>(relative: string): Promise<T | null> {
  try {
    const raw = await fs.readFile(path.join(DATA_ROOT, relative), "utf-8");
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export type Partner = {
  id: string;
  name: string;
  firm: "sequoia" | "a16z" | "ycombinator";
  role: string;
  x_handle: string | null;
  linkedin_url: string | null;
  blog_url: string | null;
  bio: string;
};

export type Company = {
  id: string;
  name: string;
  website: string | null;
  sector: string | null;
  stage: string;
  invested_by: string[];
  founder_ids: string[];
  description: string;
  linkedin_company_url: string | null;
};

export type FirmGraph = {
  partners: Partner[];
  companies: Company[];
  blog_posts: { id: string; title: string; source_url: string }[];
};

export type DigestCard = {
  signal: {
    id: string;
    kind: string;
    score: number;
    evidence: Record<string, unknown>;
    detected_at: string;
  };
  headline: string;
  one_liner: string;
  evidence_chips: string[];
  drill_down_url: string;
};

export type Digest = {
  generated_at: string;
  meta: Record<string, unknown>;
  cards: DigestCard[];
};

export const loadDigest = () => readJson<Digest>("digest.json");
export const loadFirmGraph = () => readJson<FirmGraph>("firm_graph.json");

export const slugify = (name: string) =>
  name.toLowerCase().trim().replace(/\s+/g, "-");
