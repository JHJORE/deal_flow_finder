import type { PartnerProfileDTO } from "./api/partners";
import type {
  Belief,
  Company,
  Filing,
  Firm,
  FirmId,
  Follow,
  Founder,
  Partner,
  PartnerBeliefs,
  Signal,
  Theme,
  ThemeKey,
  TopPost,
  TopicRow,
} from "./types";

export const PERIODS = ["Dec", "Jan", "Feb", "Mar", "Apr", "May"];

export const FIRMS: Record<FirmId, Firm> = {
  sequoia: { id: "sequoia", name: "Sequoia" },
  a16z: { id: "a16z", name: "a16z" },
  yc: { id: "yc", name: "Y Combinator" },
};

export const THEMES: Theme[] = [
  { key: "agents", label: "AI agents", hue: 50, share: [14, 17, 21, 26, 33, 39], age: "live 7 mo", trend: "rising" },
  { key: "voice", label: "Voice AI", hue: 155, share: [5, 6, 7, 11, 17, 23], age: "live 4 mo", trend: "rising" },
  { key: "defense", label: "Defense tech", hue: 252, share: [7, 8, 8, 10, 13, 17], age: "live 5 mo", trend: "rising" },
  { key: "evals", label: "Agent eval / reliability", hue: 305, share: [3, 4, 5, 7, 11, 16], age: "live 3 mo", trend: "rising" },
  { key: "ondevice", label: "On-device small models", hue: 85, share: [2, 2, 3, 3, 5, 9], age: "contrarian · 2 mo", trend: "rising" },
  { key: "crypto", label: "Crypto infra", hue: 30, chroma: 0.02, share: [16, 14, 12, 11, 9, 7], age: "cooling", trend: "cooling" },
];

export const themeByKey = (k: ThemeKey) => THEMES.find((t) => t.key === k)!;
export const themeColor = (t: Theme) =>
  `oklch(72% ${t.chroma ?? 0.14} ${t.hue})`;

// ---------- partner mapping from backend JSON ----------
//
// PARTNERS is populated by <PartnersProvider> after fetching the three firms'
// /api/firms/{domain}/partner-profiles endpoints. We use a live module binding
// so existing components that `import { PARTNERS, partnerById }` keep working
// — once the provider sets it, the next render reads the populated array.
//
// Field-by-field source convention (see buildPartnersFromProfiles below):
//   ✓ "from JSON"               → backend partner-profiles endpoint
//   • "HARDCODED — no data"     → static placeholder (firm phone, checkSize copy)
//   ◇ "HARDCODED — mock"        → deterministic mock from name hash (engagement)

const slug = (n: string) =>
  n.toLowerCase().replace(/[^a-z ]/g, "").trim().replace(/ +/g, "-");

export const FIRM_META: Record<FirmId, { domain: string; phone: string }> = {
  sequoia: { domain: "sequoiacap.com", phone: "+1 650-854-3927" },
  a16z: { domain: "a16z.com", phone: "+1 650-561-6750" },
  yc: { domain: "ycombinator.com", phone: "+1 650-308-9889" },
};

const THEME_KEYS: ThemeKey[] = ["agents", "voice", "defense", "evals", "ondevice", "crypto"];

function hashStr(s: string): number {
  let h = 2166136261 >>> 0; // FNV-1a
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h >>> 0;
}

function seededRand(seed: number): () => number {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 0xffffffff;
  };
}

type MockEngagement = Pick<Partner, "posts" | "engageRate" | "spike" | "engages" | "newTopic" | "topics">;

// Deterministic mock engagement so every JSON partner has the same fake
// metrics across reloads. Replace with real metrics when we have them.
function mockEngagementFor(name: string): MockEngagement {
  const rand = seededRand(hashStr(name));
  const basePosts = 4 + Math.floor(rand() * 18);
  const trend = rand() > 0.7 ? "spike" : "flat";
  const posts: number[] = [];
  let p = basePosts;
  for (let i = 0; i < 6; i++) {
    if (trend === "spike" && i >= 4) p = Math.floor(p * (1.4 + rand() * 0.6));
    else p = Math.max(1, p + Math.floor((rand() - 0.5) * 4));
    posts.push(p);
  }
  const baseEng = 14 + Math.floor(rand() * 30);
  const engageRate: number[] = [];
  let e = baseEng;
  for (let i = 0; i < 6; i++) {
    if (trend === "spike" && i >= 4) e = Math.floor(e * (1.3 + rand() * 0.5));
    else e = Math.max(5, e + Math.floor((rand() - 0.5) * 4));
    engageRate.push(e);
  }
  const pickCount = 1 + Math.floor(rand() * 3);
  const engages: ThemeKey[] = [];
  while (engages.length < pickCount) {
    const k = THEME_KEYS[Math.floor(rand() * (THEME_KEYS.length - 1))]; // skip crypto in last slot bias
    if (!engages.includes(k)) engages.push(k);
  }
  const newTopic = trend === "spike" ? themeByKey(engages[0]).label : null;
  const topics: TopicRow[] = engages.slice(0, 4).map((k, i) => ({
    t: themeByKey(k).label,
    w: 40 - i * 8 + Math.floor(rand() * 6),
    chg: Math.floor((rand() - 0.4) * 18),
    isNew: i === 0 && trend === "spike",
  }));
  return {
    posts,
    engageRate,
    spike: trend === "spike",
    engages,
    newTopic,
    topics,
  };
}

function xHandleFromUrl(url: string | null): string {
  if (!url) return "";
  const m = url.match(/(?:x\.com|twitter\.com)\/([A-Za-z0-9_]{1,15})/i);
  return m ? `@${m[1]}` : "";
}

function linkedinFromUrl(url: string | null): string {
  if (!url) return "";
  return url.replace(/^https?:\/\/(www\.)?/i, "").replace(/\/+$/, "");
}

function checkSizeFor(role: string | null): string {
  const r = (role || "").toLowerCase();
  if (r.includes("growth") || r.includes("late")) {
    return "Growth and late-stage; leads Series C and beyond.";
  }
  if (r.includes("partner") || r.includes("director")) {
    return "Seed through Series B; typically leads or co-leads.";
  }
  return "Stage focus varies; see profile and recent deals.";
}

function focusFrom(profile: PartnerProfileDTO): string {
  if (profile.focus_areas?.length) return profile.focus_areas.join(" · ");
  if (profile.teams?.length) return profile.teams.join(" · ");
  return "";
}

// Build a UI-shape Partner from one JSON profile + the firm it belongs to.
// Comments mark which fields are real (✓) vs hardcoded (•) vs mocked (◇).
export function buildPartnersFromProfiles(
  profiles: PartnerProfileDTO[],
  firm: FirmId
): Partner[] {
  const fm = FIRM_META[firm];
  return profiles.map((p) => {
    const fallbackAbout = (p.bio || "").trim().slice(0, 220);
    return {
      id: slug(p.name),                           // ✓ from JSON (slug of name)
      name: p.name,                               // ✓ from JSON
      firm,                                       // ✓ from JSON file selection
      role: p.role_display || p.role || "Partner", // ✓ from JSON
      focus: focusFrom(p),                        // ✓ from JSON (a16z + sequoia only)
      photoUrl: p.photo_url,                      // ✓ from JSON
      contact: {
        email: p.email ?? "",                     // ✓ from JSON ("" → rendered as em-dash)
        linkedin: linkedinFromUrl(p.linkedin_url), // ✓ from JSON
        x: xHandleFromUrl(p.x_url),               // ✓ from JSON
        phone: fm.phone,                          // • HARDCODED — no phone in source data
      },
      about: p.about_short || fallbackAbout,      // ✓ from JSON (Gemini-summarized; bio fallback)
      checkSize: checkSizeFor(p.role),            // • HARDCODED — no check-size in source data
      ...mockEngagementFor(p.name),               // ◇ HARDCODED — deterministic mock until we have metrics
    };
  });
}

// PARTNERS starts empty and is populated by PartnersProvider on mount.
// Components keep importing PARTNERS / partnerById and re-render once the
// provider's loaded flag flips (via context) — ES module live bindings.
export let PARTNERS: Partner[] = [];

export function _setPartners(list: Partner[]) {
  PARTNERS = list;
}

export const FOUNDERS: Founder[] = [
  { id: "f1", name: "Maya Okafor", handle: "@mayaokafor", role: "Founder, stealth · ex-Stripe ML",
    engages: ["agents", "evals"], posts: [3, 3, 4, 7, 12, 18],
    engageRate: [8, 9, 11, 16, 28, 44], followerGrowth: "+240%",
    topics: [
      { t: "Agent reliability", w: 48, chg: 17, isNew: true },
      { t: "Eval infra", w: 30, chg: 12, isNew: false },
      { t: "Stripe / payments", w: 14, chg: -9, isNew: false },
      { t: "Personal", w: 8, chg: -2, isNew: false },
    ] },
  { id: "f2", name: "Devin Nunes-Park", handle: "@devnp", role: "Founder · voice + defense AI",
    engages: ["voice", "defense"], posts: [5, 5, 6, 9, 14, 16],
    engageRate: [10, 11, 13, 18, 26, 30], followerGrowth: "+180%",
    topics: [
      { t: "Voice agents", w: 42, chg: 13, isNew: false },
      { t: "Defense AI", w: 28, chg: 10, isNew: false },
      { t: "Latency / infra", w: 18, chg: 6, isNew: false },
      { t: "Personal", w: 12, chg: -3, isNew: false },
    ] },
  { id: "f3", name: "Lena Cho", handle: "@lenacho", role: "Operator watchlist · ex-infra lead",
    engages: ["agents", "voice"], posts: [2, 2, 3, 3, 6, 11],
    engageRate: [5, 6, 6, 7, 14, 24], followerGrowth: "+95%",
    topics: [
      { t: "AI agents", w: 40, chg: 14, isNew: true },
      { t: "Voice AI", w: 30, chg: 11, isNew: false },
      { t: "Infra / data", w: 20, chg: -6, isNew: false },
      { t: "Personal", w: 10, chg: -3, isNew: false },
    ] },
  { id: "f4", name: "Arjun Reddy", handle: "@arjunbuilds", role: "Founder · agent dev tools",
    engages: ["agents"], posts: [4, 5, 5, 8, 13, 19],
    engageRate: [9, 10, 12, 17, 30, 46], followerGrowth: "+210%",
    topics: [
      { t: "Agent dev tools", w: 50, chg: 16, isNew: false },
      { t: "Eval / testing", w: 26, chg: 11, isNew: false },
      { t: "Open source", w: 16, chg: 5, isNew: false },
      { t: "Personal", w: 8, chg: -2, isNew: false },
    ] },
  { id: "f5", name: "Priya Anand", handle: "@priyabuilds", role: "Founder · agent eval infra",
    engages: ["evals", "agents"], posts: [3, 3, 4, 6, 9, 15],
    engageRate: [7, 8, 9, 13, 21, 35], followerGrowth: "+160%",
    topics: [
      { t: "Eval infrastructure", w: 46, chg: 18, isNew: true },
      { t: "Agent reliability", w: 30, chg: 12, isNew: false },
      { t: "Benchmarks", w: 16, chg: 6, isNew: false },
      { t: "Personal", w: 8, chg: -2, isNew: false },
    ] },
  { id: "f6", name: "Tomas Wexler", handle: "@twexler", role: "Founder · voice agents for ops",
    engages: ["voice"], posts: [6, 6, 7, 8, 10, 12],
    engageRate: [12, 13, 13, 15, 18, 21], followerGrowth: "+55%",
    topics: [
      { t: "Voice agents", w: 44, chg: 9, isNew: false },
      { t: "Ops automation", w: 28, chg: 7, isNew: false },
      { t: "Telephony infra", w: 18, chg: 1, isNew: false },
      { t: "Personal", w: 10, chg: -3, isNew: false },
    ] },
  { id: "f7", name: "Hannah Berg", handle: "@hannahberg", role: "Operator watchlist · ex-FAIR researcher",
    engages: ["agents"], posts: [1, 1, 2, 2, 3, 7],
    engageRate: [3, 4, 4, 5, 8, 17], followerGrowth: "+70%",
    topics: [
      { t: "Agent research", w: 42, chg: 15, isNew: true },
      { t: "Open models", w: 30, chg: 9, isNew: false },
      { t: "RL / training", w: 20, chg: 1, isNew: false },
      { t: "Personal", w: 8, chg: -2, isNew: false },
    ] },
  { id: "f8", name: "Marco Idris", handle: "@marcoidris", role: "Founder · defense autonomy",
    engages: ["defense"], posts: [4, 4, 5, 5, 7, 9],
    engageRate: [8, 9, 9, 10, 13, 17], followerGrowth: "+85%",
    topics: [
      { t: "Defense autonomy", w: 48, chg: 10, isNew: false },
      { t: "Hardware", w: 26, chg: 1, isNew: false },
      { t: "Edge compute", w: 18, chg: 6, isNew: false },
      { t: "Personal", w: 8, chg: -2, isNew: false },
    ] },
  { id: "f9", name: "Sara Lindqvist", handle: "@saralind", role: "Founder · contrarian: on-device small models",
    engages: ["ondevice"], posts: [5, 6, 6, 9, 14, 21],
    engageRate: [10, 11, 13, 19, 33, 52], followerGrowth: "+230%",
    topics: [
      { t: "On-device models", w: 50, chg: 19, isNew: true },
      { t: "Efficiency / quantization", w: 28, chg: 12, isNew: false },
      { t: "Privacy-first AI", w: 16, chg: 6, isNew: false },
      { t: "Personal", w: 6, chg: -2, isNew: false },
    ] },
];

// ---------- companies (raw, then enriched) ----------
// Deal.partner references use partner slugs (slug(name)) — must match the
// ids produced by buildPartnersFromProfiles. Same for SIGNALS.actors, FOLLOWS.
const COMPANIES_RAW: Omit<Company, "contact" | "about">[] = [
  { id: "c1", name: "Harvey", firm: "sequoia", founder: "Winston Weinberg", sector: "Legal AI",
    stage: "Series D", founderTracked: null, themeKeys: ["agents", "evals"],
    deal: { partner: "pat-grady", round: "Series D", invested: "$80M", ownership: "~12%",
      valuation: "$3.0B post-money", dealDate: "Apr 2026", lead: true },
    jobs: [18, 19, 22, 21, 38, 57],
    seniorHires: [
      { role: "First CFO", name: "hired May 2026", hot: true },
      { role: "VP Sales", name: "hired Apr 2026", hot: true },
    ],
    note: "Job postings up sharply over the last two periods and a first CFO just landed. Both point to an imminent or just-closed round." },
  { id: "c2", name: "Mistral AI", firm: "a16z", founder: "Arthur Mensch", sector: "Open models",
    stage: "Series C", founderTracked: null, themeKeys: ["ondevice", "agents"],
    deal: { partner: "anjney-midha", round: "Series C", invested: "$45M", ownership: "~6%",
      valuation: "$6.2B post-money", dealDate: "Nov 2025", lead: false },
    jobs: [40, 42, 44, 43, 46, 49],
    seniorHires: [{ role: "VP Policy", name: "hired Mar 2026", hot: false }],
    note: "Steady, healthy hiring with no anomaly. Consistent scale-up, not a fresh-round spike." },
  { id: "c3", name: "Cursor", firm: "a16z", founder: "Michael Truell", sector: "AI dev tools",
    stage: "Series B", founderTracked: null, themeKeys: ["agents", "evals"],
    deal: { partner: "martin-casado", round: "Series B", invested: "$60M", ownership: "~15%",
      valuation: "$2.5B post-money", dealDate: "Mar 2026", lead: true },
    jobs: [12, 14, 15, 19, 31, 44],
    seniorHires: [
      { role: "First General Counsel", name: "hired May 2026", hot: true },
      { role: "Head of Enterprise", name: "hired Apr 2026", hot: true },
    ],
    note: "A first General Counsel plus a hiring surge is a textbook fundraise-prep pattern." },
  { id: "c4", name: "Decagon", firm: "a16z", founder: "Jesse Zhang", sector: "Voice / support AI",
    stage: "Series A", founderTracked: null, themeKeys: ["voice"],
    deal: { partner: "anish-acharya", round: "Series A", invested: "$18M", ownership: "~18%",
      valuation: "$120M post-money", dealDate: "May 2026", lead: true },
    jobs: [8, 9, 9, 11, 16, 24],
    seniorHires: [{ role: "First VP Sales", name: "hired May 2026", hot: true }],
    note: "First VP Sales hire and rising postings; an early company stepping on the gas." },
  { id: "c5", name: "Sierra", firm: "sequoia", founder: "Bret Taylor", sector: "Agent platform",
    stage: "Series B", founderTracked: null, themeKeys: ["agents"],
    deal: { partner: "konstantine-buhler", round: "Series B", invested: "$55M", ownership: "~10%",
      valuation: "$4.5B post-money", dealDate: "Dec 2025", lead: false },
    jobs: [22, 24, 26, 28, 33, 41],
    seniorHires: [{ role: "VP Marketing", name: "hired Apr 2026", hot: false }],
    note: "Gradual hiring acceleration; worth watching but no single-period spike yet." },
  { id: "c6", name: "Parallax Labs", firm: "a16z", founder: "Arjun Reddy", sector: "Agent dev tools",
    stage: "Seed (undisclosed)", founderTracked: "f4", themeKeys: ["agents", "evals"],
    deal: { partner: "martin-casado", round: "Seed", invested: "$3.5M (of $8.5M round)", ownership: "not disclosed",
      valuation: "~$40M post-money (est.)", dealDate: "Apr 2026", lead: true },
    jobs: [1, 1, 2, 3, 7, 14],
    seniorHires: [{ role: "Founding engineers", name: "cluster hired May 2026", hot: true }],
    note: "Tied to the undisclosed Form D. Hiring from near-zero to a real team in two periods; consistent with a just-closed seed round." },
  { id: "c7", name: "Cartesia", firm: "yc", founder: "Karan Goel", sector: "Voice AI infra",
    stage: "Series A", founderTracked: null, themeKeys: ["voice"],
    deal: { partner: "garry-tan", round: "Seed (YC)", invested: "$500K", ownership: "~7%",
      valuation: "$25M post-money", dealDate: "W25 batch", lead: false },
    jobs: [6, 7, 8, 10, 15, 23],
    seniorHires: [{ role: "First Head of Product", name: "hired May 2026", hot: true }],
    note: "Voice-infra company hiring fast and bringing on a first Head of Product." },
  { id: "c8", name: "Lightdash", firm: "yc", founder: "Oliver Laslett", sector: "Data / BI",
    stage: "Series A", founderTracked: null, themeKeys: ["agents"],
    deal: { partner: "jared-friedman", round: "Seed (YC)", invested: "$500K", ownership: "~7%",
      valuation: "$18M post-money", dealDate: "S24 batch", lead: false },
    jobs: [11, 11, 12, 11, 12, 13],
    seniorHires: [],
    note: "Flat hiring, no senior-hire activity. Quiet; no fundraise signal at present." },
];

export const COMPANY_TOPICS: Record<string, TopicRow[]> = {
  c1: [
    { t: "Agent reliability", w: 42, chg: 14, themeKey: "agents", isNew: false },
    { t: "Legal workflow automation", w: 33, chg: 6, themeKey: "agents", isNew: false },
    { t: "Evaluation & accuracy", w: 18, chg: 9, themeKey: "evals", isNew: true },
    { t: "Enterprise security", w: 7, chg: -2, themeKey: null, isNew: false },
  ],
  c2: [
    { t: "Open-weight models", w: 46, chg: 5, themeKey: "ondevice", isNew: false },
    { t: "On-device inference", w: 27, chg: 11, themeKey: "ondevice", isNew: true },
    { t: "Multilingual AI", w: 19, chg: 3, themeKey: null, isNew: false },
    { t: "Developer tooling", w: 8, chg: 1, themeKey: "agents", isNew: false },
  ],
  c3: [
    { t: "AI coding agents", w: 48, chg: 17, themeKey: "agents", isNew: false },
    { t: "Codebase context & retrieval", w: 29, chg: 8, themeKey: "agents", isNew: false },
    { t: "Agent eval & correctness", w: 16, chg: 12, themeKey: "evals", isNew: true },
    { t: "Enterprise rollout", w: 7, chg: 4, themeKey: null, isNew: false },
  ],
  c4: [
    { t: "Voice support agents", w: 51, chg: 13, themeKey: "voice", isNew: false },
    { t: "Customer-experience AI", w: 28, chg: 5, themeKey: "voice", isNew: false },
    { t: "Agent reliability", w: 15, chg: 7, themeKey: "agents", isNew: true },
    { t: "Analytics", w: 6, chg: -1, themeKey: null, isNew: false },
  ],
  c5: [
    { t: "Agent platforms", w: 44, chg: 9, themeKey: "agents", isNew: false },
    { t: "Conversational AI", w: 30, chg: 4, themeKey: "voice", isNew: false },
    { t: "Enterprise deployment", w: 18, chg: 6, themeKey: null, isNew: false },
    { t: "Agent evaluation", w: 8, chg: 5, themeKey: "evals", isNew: true },
  ],
  c6: [
    { t: "Agent developer tools", w: 55, chg: 22, themeKey: "agents", isNew: true },
    { t: "Agent evaluation", w: 30, chg: 15, themeKey: "evals", isNew: true },
    { t: "Open infrastructure", w: 15, chg: 8, themeKey: null, isNew: false },
  ],
  c7: [
    { t: "Voice AI infrastructure", w: 53, chg: 16, themeKey: "voice", isNew: false },
    { t: "Low-latency speech models", w: 31, chg: 10, themeKey: "voice", isNew: true },
    { t: "Developer APIs", w: 16, chg: 4, themeKey: "agents", isNew: false },
  ],
  c8: [
    { t: "Data & BI tooling", w: 50, chg: 2, themeKey: null, isNew: false },
    { t: "Analytics agents", w: 27, chg: 6, themeKey: "agents", isNew: true },
    { t: "Open-source BI", w: 23, chg: 1, themeKey: null, isNew: false },
  ],
};

// SIGNALS, FOLLOWS, PARTNER_BELIEFS, TOP_POSTS keyed by partner slug
// (slug(name)) to line up with buildPartnersFromProfiles ids. Founder ids
// (f1, f2…) stay unchanged.

export const SIGNALS: Signal[] = [
  { id: "s1", tier: 1, conf: "high", firms: ["a16z", "sequoia"],
    headline: "Convergence — 2 partners now follow Maya Okafor within 18 days",
    body: "Anjney Midha (a16z) and Konstantine Buhler (Sequoia) both first-followed Okafor inside an 18-day window. Neither follows famous accounts casually. Earliest social-graph signal of a deal forming.",
    sources: ["X"], actors: ["anjney-midha", "f1"], age: "2d", score: 95 },
  { id: "s2", tier: 1, conf: "high", firms: ["a16z"],
    headline: "Undisclosed Form D — agent dev tools startup names a16z",
    body: "An EDGAR Form D lists a16z as an investor in a startup not yet on the a16z public portfolio page. Issuer profile matches Arjun Reddy’s stealth company.",
    sources: ["EDGAR"], actors: ["martin-casado", "f4"], age: "3d", score: 92, filing: "fd1" },
  { id: "s9", tier: 1, conf: "high", firms: ["sequoia"],
    headline: "Convergence — Pat Grady and Konstantine Buhler both follow Priya Anand",
    body: "Two Sequoia partners first-followed Anand within the same period. She builds agent eval infrastructure, the exact theme both partners just started writing about. Tight thesis-to-follow match.",
    sources: ["X", "VC sites"], actors: ["pat-grady", "f5"], age: "4d", score: 88 },
  { id: "s4", tier: 4, conf: "high", firms: ["sequoia", "yc"],
    headline: "Cross-firm thesis alignment — agent eval / reliability",
    body: "Pat Grady, Konstantine Buhler (Sequoia) and Jared Friedman, Pete Koomen (YC) all began writing on agent reliability and evals within three weeks. A new theme crossing two firms.",
    sources: ["VC sites", "X"], actors: ["pat-grady", "konstantine-buhler", "jared-friedman"], age: "6d", score: 84 },
  { id: "s3", tier: 1, conf: "med", firms: ["yc"],
    headline: "First mutual follow — Pete Koomen and Arjun Reddy",
    body: "First-time mutual follow between a YC group partner and a non-famous founder building agent dev tools. Often precedes a conversation by weeks.",
    sources: ["X"], actors: ["pete-koomen", "f4"], age: "5d", score: 80 },
  { id: "s10", tier: 4, conf: "med", firms: ["a16z"],
    headline: "Contrarian stance — Anjney Midha argues against the frontier-scale consensus",
    body: "Midha published longform making the case for small on-device models against the prevailing scale-is-everything view, then first-followed Sara Lindqvist, who builds exactly that. A contrarian partner placing an early marker.",
    sources: ["VC sites", "X"], actors: ["anjney-midha", "f9"], age: "7d", score: 74 },
  { id: "s5", tier: 2, conf: "med", firms: ["a16z"],
    headline: "Founder heat — Anish Acharya engagement spike, +164% in 30 days",
    body: "Acharya’s reply and like activity is up 164% vs his trailing baseline, concentrated on consumer-AI and voice founders. A normally steady partner is suddenly active.",
    sources: ["X"], actors: ["anish-acharya"], age: "7d", score: 71 },
  { id: "s6", tier: 4, conf: "med", firms: ["sequoia", "a16z", "yc"],
    headline: "Theme drift — Voice AI now discussed by partners at all three firms",
    body: "Voice AI mention share across tracked partners is up 6 points this period and now appears in the top topics of partners at Sequoia, a16z and YC.",
    sources: ["VC sites", "X"], actors: ["sonya-huang", "jonathan-lai", "garry-tan"], age: "8d", score: 67 },
  { id: "s7", tier: 2, conf: "med", firms: ["a16z"],
    headline: "Founder visibility acceleration — Devin Nunes-Park +180% posting",
    body: "Posting frequency up 180% vs trailing 30-day baseline; voice-agent narrative catching on and getting boosted by larger accounts.",
    sources: ["X", "LinkedIn"], actors: ["f2"], age: "9d", score: 63 },
  { id: "s11", tier: 3, conf: "med", firms: [],
    headline: "Top-lab departure — Hannah Berg leaves Meta FAIR",
    body: "FAIR researcher updated LinkedIn to no current employer and began posting on agent research. High-value AI-specific pre-company signal; no partner follows yet.",
    sources: ["LinkedIn", "X"], actors: ["f7"], age: "10d", score: 57 },
  { id: "s8", tier: 3, conf: "low", firms: [],
    headline: "Stealth departure — Lena Cho updates LinkedIn to “building something new”",
    body: "Operator-watchlist member changed her LinkedIn title and began engaging agent and voice themes on X. Early, low-confidence pre-company signal.",
    sources: ["LinkedIn", "X"], actors: ["f3"], age: "12d", score: 48 },
];

export const FILINGS: Record<string, Filing> = {
  fd1: {
    issuer: "Parallax Labs, Inc.",
    relatedFounder: "f4",
    relatedCompany: "c6",
    formType: "Form D — Notice of Exempt Offering of Securities",
    filedDate: "May 14, 2026",
    cik: "0002041883",
    exemption: "Rule 506(b)",
    offeringAmount: "$8,500,000",
    soldToDate: "$8,500,000",
    totalInvestors: 6,
    firstSale: "April 2026",
    industry: "Other Technology",
    state: "Delaware (incorporated) · San Francisco, CA (principal place of business)",
    namedInvestor: "a16z",
    relatedPersons: ["A. Reddy (Director, Executive Officer)", "Anonymous LLC (managing member)"],
    edgarUrl: "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=D",
    whyFlagged:
      "Parallax Labs does not appear on a16z’s public portfolio page or investment list, yet a16z is named as a participating investor in this filing. The issuer’s stated industry and SF base match the stealth profile of Arjun Reddy, a founder already showing follower and posting acceleration. This is a confirmed check ahead of any public announcement.",
    timeline: [
      { d: "April 2026", t: "First sale of securities", s: "Offering opens; first capital wired per the filing." },
      { d: "May 14, 2026", t: "Form D filed with SEC", s: "Issuer files the exempt-offering notice naming a16z." },
      { d: "May 14, 2026", t: "Flagged by Dealflow Radar", s: "Issuer cross-checked against a16z portfolio page — no match. Marked undisclosed." },
    ],
  },
};

export const FOLLOWS: Follow[] = [
  { partner: "anjney-midha", founder: "f1", firstSeen: 5 },
  { partner: "konstantine-buhler", founder: "f1", firstSeen: 5 },
  { partner: "martin-casado", founder: "f4", firstSeen: 3 },
  { partner: "pete-koomen", founder: "f4", firstSeen: 4 },
  { partner: "pat-grady", founder: "f4", firstSeen: 5 },
  { partner: "anish-acharya", founder: "f2", firstSeen: 4 },
  { partner: "jonathan-lai", founder: "f2", firstSeen: 5 },
  { partner: "jared-friedman", founder: "f3", firstSeen: 5 },
  { partner: "pat-grady", founder: "f5", firstSeen: 5 },
  { partner: "konstantine-buhler", founder: "f5", firstSeen: 5 },
  { partner: "garry-tan", founder: "f6", firstSeen: 5 },
  { partner: "shaun-maguire", founder: "f8", firstSeen: 5 },
  { partner: "anjney-midha", founder: "f9", firstSeen: 4 },
];

export const PARTNER_BELIEFS: Record<string, PartnerBeliefs> = {
  "pat-grady": {
    summary:
      "Pat Grady argues that the winning AI companies will be defined by reliability and distribution, not model quality. Long bullish on applied AI in regulated enterprise.",
    beliefs: [
      { text: "Agent reliability and evaluation, not raw capability, is the real moat in enterprise AI.", era: "recent", themeKeys: ["evals", "agents"], sources: ["X", "Sequoia essay"] },
      { text: "Distribution into regulated industries beats being first to a model.", era: "longheld", themeKeys: ["agents"], sources: ["X", "LinkedIn"] },
      { text: "Vertical AI applications will out-return horizontal infrastructure bets.", era: "longheld", themeKeys: ["agents", "evals"], sources: ["Sequoia essay"] },
    ],
  },
  "konstantine-buhler": {
    summary:
      "Konstantine Buhler frames AI agents as the next computing platform and has recently centred reliability as the gating problem.",
    beliefs: [
      { text: "Agent evaluation infrastructure is a venture-scale category in its own right.", era: "recent", themeKeys: ["evals"], sources: ["X", "Sequoia essay"] },
      { text: "Multi-agent systems will define the next platform shift.", era: "longheld", themeKeys: ["agents"], sources: ["Sequoia essay", "X"] },
      { text: "Voice will be a primary interface for agents, not a niche.", era: "recent", themeKeys: ["voice"], sources: ["X"] },
    ],
  },
  "martin-casado": {
    summary:
      "Martin Casado believes infrastructure and developer tooling capture durable value, and is sceptical of thin application-layer wrappers.",
    beliefs: [
      { text: "The agent tooling and infra layer will hold value better than the app layer.", era: "recent", themeKeys: ["agents"], sources: ["X", "a16z essay"] },
      { text: "Open systems and composable infra beat closed end-to-end platforms.", era: "longheld", themeKeys: ["agents"], sources: ["a16z essay", "LinkedIn"] },
      { text: "Data systems are still under-invested relative to model hype.", era: "longheld", themeKeys: ["agents"], sources: ["X"] },
    ],
  },
  "anish-acharya": {
    summary:
      "Anish Acharya believes consumer AI will be voice-first and that personalisation is the consumer moat.",
    beliefs: [
      { text: "Voice is the breakout consumer AI interface of the next two years.", era: "recent", themeKeys: ["voice"], sources: ["X", "a16z essay"] },
      { text: "Consumer AI products win on personalisation, not feature count.", era: "longheld", themeKeys: ["voice"], sources: ["LinkedIn", "X"] },
    ],
  },
  "anjney-midha": {
    summary:
      "Anjney Midha is a vocal contrarian on model scale: he argues small, open, on-device models are structurally undervalued.",
    beliefs: [
      { text: "Small, on-device models will capture more real-world deployment than frontier models.", era: "recent", themeKeys: ["ondevice"], sources: ["X", "a16z essay"] },
      { text: "Open models are a national-strategic priority, not just a commercial one.", era: "longheld", themeKeys: ["ondevice", "agents"], sources: ["a16z essay", "X"] },
      { text: "Defence and dual-use AI is an under-priced venture category.", era: "longheld", themeKeys: ["defense"], sources: ["X", "LinkedIn"] },
    ],
  },
  "garry-tan": {
    summary:
      "Garry Tan believes founder agency and speed matter more than market timing, and is broadly bullish on AI agents across verticals.",
    beliefs: [
      { text: "High-agency founders outperform regardless of category.", era: "longheld", themeKeys: ["agents", "voice"], sources: ["X", "LinkedIn"] },
      { text: "AI agents will reach every vertical faster than incumbents expect.", era: "recent", themeKeys: ["agents"], sources: ["X"] },
      { text: "Voice AI is a credible standalone wave, not a feature.", era: "recent", themeKeys: ["voice"], sources: ["X"] },
    ],
  },
  "jared-friedman": {
    summary:
      "Jared Friedman believes AI dev tools and reliability tooling are where early-stage software value is concentrating.",
    beliefs: [
      { text: "Agent reliability tooling is the highest-leverage early-stage software bet.", era: "recent", themeKeys: ["evals", "agents"], sources: ["X", "YC essay"] },
      { text: "Developer-first products compound advantage faster than top-down sales.", era: "longheld", themeKeys: ["agents"], sources: ["LinkedIn", "X"] },
    ],
  },
  "sonya-huang": {
    summary:
      "Sonya Huang sees AI as a genuine platform shift and maps the application layer as the durable value capture.",
    beliefs: [
      { text: "The agent application layer, not infrastructure, captures the lasting margin.", era: "recent", themeKeys: ["agents"], sources: ["Sequoia essay", "X"] },
      { text: "AI is a true platform shift on the scale of mobile or cloud.", era: "longheld", themeKeys: ["agents"], sources: ["Sequoia essay"] },
      { text: "Voice interfaces will be central to how agents reach consumers.", era: "recent", themeKeys: ["voice"], sources: ["X"] },
    ],
  },
  "shaun-maguire": {
    summary:
      "Shaun Maguire believes deep tech and defence are structurally under-funded by venture and that hard engineering is a moat.",
    beliefs: [
      { text: "Defence and dual-use deep tech is the most mispriced venture category.", era: "longheld", themeKeys: ["defense"], sources: ["X", "LinkedIn"] },
      { text: "Hard physical and engineering challenges are more defensible than software.", era: "longheld", themeKeys: ["defense"], sources: ["X"] },
    ],
  },
  "alfred-lin": {
    summary:
      "Alfred Lin believes consumer behaviour change, not technology, gates outcomes, and that great founders beat great markets.",
    beliefs: [
      { text: "Consumer adoption curves, not model capability, decide AI consumer winners.", era: "longheld", themeKeys: ["agents"], sources: ["LinkedIn", "Sequoia essay"] },
      { text: "Founder quality outweighs market timing over a fund’s life.", era: "longheld", themeKeys: ["agents"], sources: ["X"] },
    ],
  },
  "jennifer-li": {
    summary:
      "Jennifer Li believes the data and tooling layer underneath agents is where enterprise AI value compounds.",
    beliefs: [
      { text: "The data infrastructure under AI agents is undervalued relative to the apps.", era: "recent", themeKeys: ["agents", "evals"], sources: ["a16z essay", "X"] },
      { text: "Enterprise AI dev tools will consolidate into a few category leaders.", era: "longheld", themeKeys: ["agents"], sources: ["LinkedIn"] },
    ],
  },
  "jonathan-lai": {
    summary:
      "Jonathan Lai believes generative AI will reshape interactive media and that games are the leading edge of AI x creative.",
    beliefs: [
      { text: "Games and simulation are the proving ground for generative AI.", era: "longheld", themeKeys: ["agents"], sources: ["a16z essay", "X"] },
      { text: "Voice and generative media will merge into new interactive formats.", era: "recent", themeKeys: ["voice"], sources: ["X"] },
    ],
  },
  "diana-hu": {
    summary:
      "Diana Hu believes technical founders and hard AI problems (robotics, spatial, agents) produce the most defensible companies.",
    beliefs: [
      { text: "Technically deep founders building hard AI win over fast-following teams.", era: "longheld", themeKeys: ["agents"], sources: ["X", "LinkedIn"] },
      { text: "Robotics and embodied AI are approaching a venture inflection point.", era: "recent", themeKeys: ["agents"], sources: ["X"] },
    ],
  },
  "pete-koomen": {
    summary:
      "Pete Koomen believes AI-native applications must be rebuilt from scratch and that prompt-level tooling is a real category.",
    beliefs: [
      { text: "AI-native apps must be re-architected, not bolted onto existing products.", era: "recent", themeKeys: ["agents"], sources: ["X", "YC essay"] },
      { text: "Prompt and agent tooling is an under-built layer of the stack.", era: "recent", themeKeys: ["evals", "agents"], sources: ["X"] },
      { text: "The best AI applications will feel native, not like chatbots stapled on.", era: "longheld", themeKeys: ["agents"], sources: ["LinkedIn"] },
    ],
  },
};

export const TOP_POSTS: Record<string, TopPost> = {
  "pat-grady": { text: "Reliability is the new benchmark. The AI companies that win enterprise won’t have the best demos — they’ll have the fewest incidents.", when: "4d ago", likes: "3.1K", reposts: "412" },
  "sonya-huang": { text: "Every cycle the app layer gets written off as thin. Every cycle it captures the margin. Agents are no different.", when: "8d ago", likes: "2.4K", reposts: "305" },
  "shaun-maguire": { text: "The most under-priced thing in venture right now is hard engineering. Anyone can fine-tune. Almost no one can build the physical thing.", when: "6d ago", likes: "5.0K", reposts: "690" },
  "alfred-lin": { text: "Markets don’t make founders. Founders make markets. 15 years in and this is still the only pattern that holds.", when: "12d ago", likes: "4.2K", reposts: "520" },
  "konstantine-buhler": { text: "Agent evals are where infra was in 2014: obviously necessary, badly underbuilt, and about to be a category.", when: "3d ago", likes: "2.8K", reposts: "377" },
  "martin-casado": { text: "Hot take that shouldn’t be hot: most of the value in AI agents will accrue to the tooling layer, not the apps.", when: "5d ago", likes: "4.6K", reposts: "603" },
  "anish-acharya": { text: "Voice is the first interface where AI is genuinely better than the app it replaces. Consumer is about to feel very different.", when: "7d ago", likes: "3.9K", reposts: "488" },
  "jennifer-li": { text: "The data layer under agents is doing all the work and getting none of the credit. That’s usually where I want to invest.", when: "9d ago", likes: "2.1K", reposts: "266" },
  "jonathan-lai": { text: "Games have always been where new interfaces get proven. Generative AI will be no exception — watch this space.", when: "11d ago", likes: "1.9K", reposts: "231" },
  "anjney-midha": { text: "The consensus says scale wins. I think the next decade belongs to small, open, on-device models. Happy to be the contrarian here.", when: "6d ago", likes: "7.4K", reposts: "1.1K" },
  "garry-tan": { text: "High agency beats everything. Not the idea, not the market, not the timing. Find the founder who refuses to lose.", when: "2d ago", likes: "9.8K", reposts: "1.4K" },
  "jared-friedman": { text: "If you’re building agent reliability tooling, talk to me. It’s the highest-leverage thing you can build in software right now.", when: "4d ago", likes: "3.3K", reposts: "401" },
  "diana-hu": { text: "The best AI companies I see are started by people who can build the hard part themselves. Technical depth is the moat.", when: "10d ago", likes: "2.6K", reposts: "318" },
  "pete-koomen": { text: "You can’t bolt AI onto a product built for humans clicking buttons. The winners are rebuilding from the prompt up.", when: "5d ago", likes: "3.7K", reposts: "455" },
};

// ---------- companies: derived enrichment ----------
const slugCompany = (n: string) => n.toLowerCase().replace(/[^a-z ]/g, "").trim().replace(/ +/g, "");
const firstLast = (n: string) => {
  const p = n.toLowerCase().replace(/[^a-z ]/g, "").trim().split(/ +/);
  return { first: p[0] || "", last: p[p.length - 1] || "" };
};

export const COMPANIES: Company[] = COMPANIES_RAW.map((c) => {
  const dom = `${slugCompany(c.name)}.com`;
  const fn = firstLast(c.founder);
  const phoneStub = (200 + (c.id.charCodeAt(1) * 7) % 799).toString();
  const phoneTail = (10 + (c.id.charCodeAt(1) % 89)).toString();
  const article = /^[AEIOU]/.test(c.sector) ? "an " : "a ";
  const about =
    `${c.name} is ${article}${c.sector.toLowerCase()} company founded by ${c.founder}, ` +
    `currently at ${c.stage} and backed by ${FIRMS[c.firm].name}. ${c.note}`;
  return {
    ...c,
    contact: {
      email: `hello@${dom}`,
      founderEmail: `${fn.first}@${dom}`,
      phone: `+1 415-${phoneStub}-01${phoneTail}`,
      linkedin: `linkedin.com/company/${slugCompany(c.name)}`,
      x: `@${slugCompany(c.name)}`,
      site: dom,
    },
    about,
  };
});

// ---------- lookups ----------
export const partnerById = (id: string) => PARTNERS.find((p) => p.id === id);
export const founderById = (id: string) => FOUNDERS.find((f) => f.id === id);
export const companyById = (id: string) => COMPANIES.find((c) => c.id === id);
export const actorById = (id: string) => partnerById(id) || founderById(id);

export const firmColor = (id: FirmId) =>
  id === "sequoia"
    ? "var(--firm-sequoia)"
    : id === "a16z"
    ? "var(--firm-a16z)"
    : "var(--firm-yc)";

export const tierName: Record<number, string> = {
  1: "Deal forming",
  2: "Founder warming up",
  3: "New thing being built",
  4: "Consensus shifting",
};

export const tierAccent: Record<number, string> = {
  1: "var(--accent)",
  2: "var(--caution)",
  3: "var(--info)",
  4: "var(--positive)",
};

export const confAccent: Record<string, string> = {
  high: "var(--positive)",
  med: "var(--caution)",
  low: "var(--ink-3)",
};

export const initials = (n: string) =>
  n
    .split(" ")
    .map((x) => x[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

export const delta = (a: number[]) => a.map((v, i) => (i === 0 ? 0 : v - a[i - 1]));

export const isRecentDeal = (dealDate: string) =>
  /(Mar|Apr|May) 2026|W2[6-9]|S2[6-9]/.test(dealDate);

export type PredictabilityResult = {
  scored: (Belief & { backedBy: Company | null })[];
  backedCount: number;
  hasDeals: boolean;
  pct: number;
  ledDeals: Company[];
  total: number;
};

export function computePredictability(
  partnerId: string,
  window: "all" | "90"
): PredictabilityResult | null {
  const bd = PARTNER_BELIEFS[partnerId];
  if (!bd) return null;
  let ledDeals = COMPANIES.filter((c) => c.deal && c.deal.partner === partnerId);
  if (window === "90") ledDeals = ledDeals.filter((c) => isRecentDeal(c.deal.dealDate));
  const scored = bd.beliefs.map((b) => {
    const match =
      ledDeals.find((c) => (c.themeKeys || []).some((tk) => b.themeKeys.includes(tk))) ?? null;
    return { ...b, backedBy: match };
  });
  const backedCount = scored.filter((b) => b.backedBy).length;
  const hasDeals = ledDeals.length > 0;
  const pct = scored.length ? Math.round((backedCount / scored.length) * 100) : 0;
  return { scored, backedCount, hasDeals, pct, ledDeals, total: scored.length };
}
