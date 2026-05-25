import type { PartnerProfileDTO } from "./api/partners";
import type { PortfolioCompanyDTO } from "./api/portfolio";
import type {
  Belief,
  Company,
  Deal,
  Filing,
  Firm,
  FirmId,
  Follow,
  Founder,
  Partner,
  PartnerBeliefs,
  SeniorHire,
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
// PARTNERS is populated by <DataProvider> after fetching the three firms'
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
      about: (p.bio || "").trim() || p.about_short || "", // ✓ full bio from JSON; about_short is the 1-2 sentence fallback
      checkSize: checkSizeFor(p.role),            // • HARDCODED — no check-size in source data
      ...mockEngagementFor(p.name),               // ◇ HARDCODED — deterministic mock until we have metrics
    };
  });
}

// PARTNERS starts empty and is populated by DataProvider on mount.
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

// ---------- companies ----------
// COMPANIES is populated by <DataProvider> after fetching each firm's
// /api/firms/{domain}/portfolio-profiles endpoint. We use ONLY what the
// portfolio JSON gives us (name, sector, description, photo_url, website,
// linkedin_url, founders, detail_url). Everything else on the Company type
// (stage, jobs, seniorHires, themeKeys, deal, note) is filled with empty
// defaults because the portfolio JSON does not carry that information —
// views must treat those fields as "no data available".

const slugCompanyName = (n: string) =>
  n.toLowerCase().replace(/[^a-z0-9 ]/g, "").trim().replace(/ +/g, "-");

const companyId = (firm: FirmId, name: string) =>
  `${firm}-${slugCompanyName(name)}`;

// Shared illustrative placeholder applied to every JSON-derived company.
// The portfolio JSON does not carry stage / hiring / deal / topic data, so
// these fields use the SAME hardcoded example everywhere — visually demoing
// what the panels look like without pretending each company is unique.
// The footer disclaimer ("historic signal data is illustrative") covers it.
const EXAMPLE_STAGE = "Series B";
const EXAMPLE_JOBS = [18, 19, 22, 21, 38, 57];
const EXAMPLE_SENIOR_HIRES: SeniorHire[] = [
  { role: "First CFO", name: "hired May 2026", hot: true },
  { role: "VP Sales", name: "hired Apr 2026", hot: true },
];
const EXAMPLE_THEME_KEYS: ThemeKey[] = ["agents", "evals"];
const EXAMPLE_TOPICS: TopicRow[] = [
  { t: "Agent reliability", w: 42, chg: 14, themeKey: "agents", isNew: false },
  { t: "Workflow automation", w: 33, chg: 6, themeKey: "agents", isNew: false },
  { t: "Evaluation & accuracy", w: 18, chg: 9, themeKey: "evals", isNew: true },
  { t: "Enterprise security", w: 7, chg: -2, themeKey: null, isNew: false },
];
const EXAMPLE_NOTE =
  "Illustrative hiring pattern: job postings up sharply over the last two periods with a CFO and VP Sales just landing — the kind of move that often precedes a fresh round.";
// Empty partner slug → modal renders firm name as the deal backer rather
// than picking the wrong person across firms.
const EXAMPLE_DEAL: Deal = {
  partner: "",
  round: "Series B (example)",
  invested: "$45M (example)",
  ownership: "~12% (example)",
  valuation: "$600M post-money (example)",
  dealDate: "Apr 2026 (example)",
  lead: true,
};

// Build the Company list for one firm from its portfolio JSON.
// Real per-company fields (name, sector, description, photo, founders,
// website, linkedin) come from JSON. The hiring/deal/topic panels render
// the same hardcoded illustrative example for every company.
export function buildCompaniesFromPortfolio(
  profiles: PortfolioCompanyDTO[],
  firm: FirmId
): Company[] {
  return profiles.map((p) => {
    const id = companyId(firm, p.name);
    const founder = p.founders && p.founders[0] ? p.founders[0].name : "";
    const cleanLi = (u: string | null) =>
      u ? u.replace(/^https?:\/\/(www\.)?/i, "").replace(/\/+$/, "") : "";
    const cleanHost = (u: string | null) =>
      u ? u.replace(/^https?:\/\/(www\.)?/i, "").replace(/\/.*$/, "") : "";

    return {
      id,
      name: p.name,
      firm,
      founder,
      foundersList: (p.founders || []).map((f) => ({ name: f.name, role: f.role })),
      sector: p.sector || "",
      description: p.description,
      detailUrl: p.detail_url,
      website: p.website,
      linkedinUrl: p.linkedin_url,
      photoUrl: p.photo_url,
      // Shared illustrative panels (same for every company).
      stage: EXAMPLE_STAGE,
      founderTracked: null,
      themeKeys: EXAMPLE_THEME_KEYS,
      deal: EXAMPLE_DEAL,
      jobs: EXAMPLE_JOBS,
      seniorHires: EXAMPLE_SENIOR_HIRES,
      note: EXAMPLE_NOTE,
      contact: {
        email: "",
        founderEmail: "",
        phone: "",
        linkedin: cleanLi(p.linkedin_url),
        x: "",
        site: cleanHost(p.website),
      },
      about: p.description ?? "",
      topics: EXAMPLE_TOPICS,
    };
  });
}

// COMPANIES starts empty and is populated by DataProvider on mount.
// Same live-binding pattern as PARTNERS — components keep importing COMPANIES
// and re-render once the provider's loaded flag flips.
export let COMPANIES: Company[] = [];

// COMPANY_TOPICS is kept as a derived lookup keyed by company id so existing
// consumers (CompanyProfileView, ConsensusView) don't change. It's rebuilt
// whenever _setCompanies fires.
export let COMPANY_TOPICS: Record<string, TopicRow[]> = {};

export function _setCompanies(list: Company[]) {
  COMPANIES = list;
  const next: Record<string, TopicRow[]> = {};
  for (const c of list) next[c.id] = c.topics ?? [];
  COMPANY_TOPICS = next;
}


// SIGNALS, FOLLOWS, PARTNER_BELIEFS, TOP_POSTS keyed by partner slug
// (slug(name)) to line up with buildPartnersFromProfiles ids. Founder ids
// (f1, f2…) stay unchanged.

export const SIGNALS: Signal[] = [
  { id: "s1", tier: 1, conf: "high", firms: ["a16z", "sequoia"],
    headline: "Convergence — 2 partners now follow Maya Okafor within 18 days",
    body: "Anjney Midha (a16z) and Konstantine Buhler (Sequoia) both first-followed Okafor inside an 18-day window. Neither follows famous accounts casually. Earliest social-graph signal of a deal forming.",
    sources: ["X"], actors: ["anjney-midha", "f1"], age: "2d", score: 95 },
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
  { id: "s12", tier: 1, conf: "high", firms: ["a16z"],
    headline: "EDGAR Form D — a16z named in Somo Labs $23M raise",
    body: "Form D filed May 20 lists a16z’s Anish Acharya as a director of Somo Labs Inc.; full $23.25M offering reported sold. Newest confirmed a16z check pulled straight from SEC.",
    sources: ["EDGAR"], actors: ["anish-acharya"], age: "5d", score: 91, filing: "fd2" },
  { id: "s13", tier: 1, conf: "high", firms: ["sequoia"],
    headline: "EDGAR Form D — Sequoia confirms $200M Mercury check",
    body: "Mercury Technologies filed Form D on May 20 reporting a fully-subscribed $200M raise; Sonya Huang is listed as a director alongside founder Immad Akhund. Newest confirmed Sequoia check of the cycle.",
    sources: ["EDGAR"], actors: ["sonya-huang"], age: "5d", score: 90, filing: "fd3" },
  { id: "s14", tier: 1, conf: "high", firms: ["sequoia"],
    headline: "EDGAR Form D — Sequoia named in Send Cut Send $110M raise",
    body: "Andrew Reed listed as a director on a Form D filed May 20 by Send Cut Send, Inc., the on-demand laser-cutting marketplace. Full $110M offering reported sold.",
    sources: ["EDGAR"], actors: ["andrew-reed"], age: "5d", score: 89, filing: "fd4" },
];

export const FILINGS: Record<string, Filing> = {
  fd2: {
    issuer: "Somo Labs Inc.",
    relatedFounder: null,
    relatedCompany: null,
    formType: "Form D — Notice of Exempt Offering of Securities",
    filedDate: "May 20, 2026",
    cik: "0002134213",
    exemption: "Rule 506(b)",
    offeringAmount: "$23,249,939",
    soldToDate: "$22,914,951",
    totalInvestors: 0,
    firstSale: "May 2026",
    industry: "Other Technology",
    state: "Delaware (incorporated)",
    namedInvestor: "a16z",
    relatedPersons: [
      "Yuen Fai James Lo (Executive Officer, Director)",
      "Jaymin Mankowitz (Director)",
      "Anish Acharya (Director)",
      "Jeannette zu Furstenberg (Director)",
    ],
    edgarUrl:
      "https://www.sec.gov/Archives/edgar/data/2134213/000213421326000003/0002134213-26-000003-index.htm",
    whyFlagged:
      "Anish Acharya is named as a director on the Form D — confirmation that a16z is on the cap table. The $23.25M raise is fully subscribed, with the filing dated five days ago.",
    timeline: [
      { d: "May 2026", t: "First sale of securities", s: "Offering opens; first capital wired per the filing." },
      { d: "May 20, 2026", t: "Form D filed with SEC", s: "Issuer files the exempt-offering notice; Anish Acharya listed as a director." },
      { d: "May 20, 2026", t: "Flagged by Dealflow Radar", s: "EDGAR sweep picked up Acharya’s name in the related-persons list." },
    ],
  },
  fd3: {
    issuer: "Mercury Technologies, Inc.",
    relatedFounder: null,
    relatedCompany: null,
    formType: "Form D — Notice of Exempt Offering of Securities",
    filedDate: "May 20, 2026",
    cik: "0001719932",
    exemption: "Rule 506(b)",
    offeringAmount: "$199,999,824",
    soldToDate: "$199,999,824",
    totalInvestors: 0,
    firstSale: "May 2026",
    industry: "Commercial Banking / FinTech",
    state: "Delaware (incorporated)",
    namedInvestor: "Sequoia",
    relatedPersons: [
      "Immad Akhund (Executive Officer, Director)",
      "Jason Zhang (Executive Officer, Director)",
      "Saar Gur (Director)",
      "Sonya Huang (Director)",
      "Tim Mayopoulos (Director)",
    ],
    edgarUrl:
      "https://www.sec.gov/Archives/edgar/data/1719932/000171993226000001/0001719932-26-000001-index.htm",
    whyFlagged:
      "Newest confirmed Sequoia check this cycle. Sonya Huang is named as a director on Mercury’s Form D, with the full $200M offering reported as sold.",
    timeline: [
      { d: "May 2026", t: "First sale of securities", s: "Offering opens; full $200M subscribed per the filing." },
      { d: "May 20, 2026", t: "Form D filed with SEC", s: "Issuer files the exempt-offering notice; Sonya Huang listed as a director." },
      { d: "May 20, 2026", t: "Flagged by Dealflow Radar", s: "EDGAR sweep picked up Huang’s name in the related-persons list." },
    ],
  },
  fd4: {
    issuer: "Send Cut Send, Inc.",
    relatedFounder: null,
    relatedCompany: null,
    formType: "Form D — Notice of Exempt Offering of Securities",
    filedDate: "May 20, 2026",
    cik: "0002131876",
    exemption: "Rule 506(b)",
    offeringAmount: "$110,000,000",
    soldToDate: "$110,000,000",
    totalInvestors: 0,
    firstSale: "May 2026",
    industry: "Manufacturing",
    state: "Delaware (incorporated)",
    namedInvestor: "Sequoia",
    relatedPersons: [
      "James Belosic (Chief Executive Officer, Director)",
      "Erin Belosic (President, Director)",
      "Jacob Graham (Chief Technology Officer, Director)",
      "Mark Sugarman (Director)",
      "Andrew Reed (Director)",
    ],
    edgarUrl:
      "https://www.sec.gov/Archives/edgar/data/2131876/000213187626000001/0002131876-26-000001-index.htm",
    whyFlagged:
      "Andrew Reed is named as a director on Send Cut Send’s Form D — confirming Sequoia’s seat on the on-demand laser-cutting marketplace. Full $110M offering reported sold.",
    timeline: [
      { d: "May 2026", t: "First sale of securities", s: "Offering opens; full $110M subscribed per the filing." },
      { d: "May 20, 2026", t: "Form D filed with SEC", s: "Issuer files the exempt-offering notice; Andrew Reed listed as a director." },
      { d: "May 20, 2026", t: "Flagged by Dealflow Radar", s: "EDGAR sweep picked up Reed’s name in the related-persons list." },
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
  "abhishek-malani": {
    summary:
      "Abhishek Malani is a growth-stage Sequoia investor based in New York, focused on capital-efficient vertical AI and fintech category leaders.",
    beliefs: [
      { text: "New York will produce the next generation of vertical AI and fintech category leaders.", era: "recent", themeKeys: ["agents"], sources: ["X", "LinkedIn"] },
      { text: "Capital-efficient growth — not blitz-scaling — defines the winners of this cycle.", era: "longheld", themeKeys: ["agents"], sources: ["LinkedIn"] },
      { text: "Founder candor and direct feedback shorten the time to product-market fit.", era: "longheld", themeKeys: ["agents"], sources: ["Sequoia essay"] },
    ],
  },
  "anas-biad": {
    summary:
      "Anas Biad is a growth-stage Sequoia partner who pairs ex-Bain and ex-Silver Lake discipline with a founder-first thesis on late-stage tech.",
    beliefs: [
      { text: "Discipline on late-stage pricing matters more than category enthusiasm.", era: "longheld", themeKeys: ["agents"], sources: ["LinkedIn"] },
      { text: "Founder character compounds across decades; markets do not.", era: "longheld", themeKeys: ["agents"], sources: ["Sequoia essay", "X"] },
      { text: "European technical talent is structurally undervalued in growth-stage portfolios.", era: "recent", themeKeys: ["agents", "evals"], sources: ["X"] },
    ],
  },
  "andrew-reed": {
    summary:
      "Andrew Reed backs globally distributed, remote-native founders building durable software — from Bolt in Tallinn to Rappi in Bogotá to Zapier and Loom.",
    beliefs: [
      { text: "The next decade of category-defining software will be built outside Silicon Valley.", era: "recent", themeKeys: ["agents"], sources: ["X", "Sequoia essay"] },
      { text: "Remote-native organisations out-execute office-bound competitors on focused product.", era: "longheld", themeKeys: ["agents"], sources: ["LinkedIn"] },
      { text: "Trusted dialogue and fast response are themselves a competitive edge for an investor.", era: "longheld", themeKeys: ["evals"], sources: ["X"] },
    ],
  },
  "bill-coughran": {
    summary:
      "Bill Coughran invests in deep technical infrastructure — networking, security, ML/AI — drawing on his decades running engineering at Google.",
    beliefs: [
      { text: "The most defensible AI companies are built on hard systems problems, not on prompts.", era: "recent", themeKeys: ["evals", "agents"], sources: ["Sequoia essay"] },
      { text: "Networking, security, and ML are converging into a single infrastructure layer.", era: "longheld", themeKeys: ["agents"], sources: ["X", "Sequoia essay"] },
      { text: "Day-to-day technical mentorship separates good operators from great ones.", era: "longheld", themeKeys: ["evals"], sources: ["LinkedIn"] },
    ],
  },
  "alex-immerman": {
    summary:
      "Alex Immerman leads growth-stage a16z investments at the intersection of AI, consumer, B2B, crypto, and the physical world (ElevenLabs, Flock Safety, Waymo, Stripe).",
    beliefs: [
      { text: "Frontier AI applications will keep producing growth-stage outliers in unexpected verticals.", era: "recent", themeKeys: ["agents"], sources: ["a16z essay", "X"] },
      { text: "Companies bridging the digital and physical world are structurally undervalued.", era: "longheld", themeKeys: ["defense", "agents"], sources: ["a16z essay"] },
      { text: "Growth investing is a craft of pattern recognition, not spreadsheet output.", era: "longheld", themeKeys: ["agents"], sources: ["LinkedIn"] },
    ],
  },
  "alex-rampell": {
    summary:
      "Alex Rampell leads a16z's $1B Apps practice across B2B and B2C and is a serial fintech founder (Affirm with Max Levchin, TrialPay acquired by Visa).",
    beliefs: [
      { text: "Distribution will keep beating better technology in consumer fintech.", era: "longheld", themeKeys: ["agents"], sources: ["a16z essay", "X"] },
      { text: "Vertical SaaS that captures payments is the most under-priced enterprise category.", era: "recent", themeKeys: ["agents"], sources: ["X"] },
      { text: "Founders who have shipped before iterate 10x faster than first-time builders.", era: "longheld", themeKeys: ["agents"], sources: ["LinkedIn"] },
    ],
  },
  "ali-yahya": {
    summary:
      "Ali Yahya is a crypto general partner at a16z investing across infrastructure and applications; backed Alchemy, EigenLayer, LayerZero, and Solana.",
    beliefs: [
      { text: "Restaking and shared security will be foundational to the next decade of crypto infrastructure.", era: "recent", themeKeys: ["crypto"], sources: ["a16z essay", "X"] },
      { text: "Decentralised networks better align incentives on the open internet.", era: "longheld", themeKeys: ["crypto"], sources: ["a16z essay"] },
      { text: "Crypto infrastructure remains under-priced in current sentiment.", era: "recent", themeKeys: ["crypto"], sources: ["X"] },
    ],
  },
  "andrew-chen": {
    summary:
      "Andrew Chen runs a16z speedrun across tech, entertainment, and AI; ex-Rider Growth lead at Uber and author of The Cold Start Problem.",
    beliefs: [
      { text: "AI consumer products are a network-effects business; cold-start matters more than features.", era: "recent", themeKeys: ["voice", "agents"], sources: ["a16z essay", "X"] },
      { text: "Voice AI is a credible standalone consumer wave, not just a UI feature.", era: "recent", themeKeys: ["voice"], sources: ["X"] },
      { text: "Distribution loops compound; product alone does not.", era: "longheld", themeKeys: ["agents"], sources: ["andrewchen.com"] },
    ],
  },
  "andy-mccall": {
    summary:
      "Andy McCall invests across a16z's American Dynamism, enterprise, and fintech practices, with a thesis on companies serving the national interest.",
    beliefs: [
      { text: "Companies serving the national interest are an emerging venture category, not a niche.", era: "longheld", themeKeys: ["defense"], sources: ["a16z essay"] },
      { text: "Defence and dual-use AI is structurally under-funded relative to the strategic opportunity.", era: "recent", themeKeys: ["defense"], sources: ["X"] },
    ],
  },
  "aaron-epstein": {
    summary:
      "Aaron Epstein is a YC general partner with a creator-economy operator background; previously co-founded Creative Market (YC W10, acquired by Autodesk).",
    beliefs: [
      { text: "Creator-economy infra is where the next AI applications find their first paying users.", era: "recent", themeKeys: ["agents"], sources: ["YC essay", "X"] },
      { text: "Founders who have built a marketplace once understand cold-start in a way investors rarely do.", era: "longheld", themeKeys: ["agents"], sources: ["LinkedIn"] },
      { text: "Design quality is itself a distribution advantage for creator tools.", era: "longheld", themeKeys: ["voice"], sources: ["X"] },
    ],
  },
  "andrew-miklas": {
    summary:
      "Andrew Miklas backs technical founders on infrastructure and developer tools; previously the founding CTO of PagerDuty (YC S10, NYSE:PD).",
    beliefs: [
      { text: "Agent reliability tooling is the highest-leverage early-stage software bet for the next two years.", era: "recent", themeKeys: ["evals", "agents"], sources: ["YC essay", "X"] },
      { text: "Resilient systems thinking is the moat for early-stage infrastructure companies.", era: "longheld", themeKeys: ["evals"], sources: ["LinkedIn"] },
      { text: "Developer-first products compound advantage faster than top-down enterprise sales.", era: "longheld", themeKeys: ["agents"], sources: ["X"] },
    ],
  },
  "ankit-gupta": {
    summary:
      "Ankit Gupta backs ML-meets-bio founders and deep-learning-native infrastructure; previously co-founded Reverie Labs, acquired by Ginkgo Bioworks in 2024.",
    beliefs: [
      { text: "Foundation models tailored to scientific data will out-perform general-purpose models in drug discovery.", era: "recent", themeKeys: ["agents"], sources: ["YC essay", "X"] },
      { text: "Technical co-founders willing to publish research are an under-priced filter for early-stage betting.", era: "longheld", themeKeys: ["agents", "evals"], sources: ["LinkedIn"] },
      { text: "ML in regulated industries needs purpose-built evaluation infrastructure, not generic benchmarks.", era: "recent", themeKeys: ["evals"], sources: ["X"] },
    ],
  },
  "brad-flora": {
    summary:
      "Brad Flora is an early-stage YC partner and active angel investor across hundreds of startups; previously co-founded and led Perfect Audience (YC 2011, acquired by Marin Software).",
    beliefs: [
      { text: "Distribution channels still mint companies faster than novel models.", era: "recent", themeKeys: ["agents"], sources: ["X"] },
      { text: "Angel investing across hundreds of companies sharpens pattern recognition more than any framework.", era: "longheld", themeKeys: ["agents"], sources: ["LinkedIn"] },
    ],
  },
  "david-lieb": {
    summary:
      "David Lieb is a consumer-focused YC general partner; previously co-founded Bump (YC S09, acquired by Google) and helped shape what became Google Photos.",
    beliefs: [
      { text: "Consumer AI products win on intuition for the everyday moment, not on benchmark scores.", era: "recent", themeKeys: ["voice", "agents"], sources: ["X"] },
      { text: "The best consumer founders ship the simple thing first, then expand from there.", era: "longheld", themeKeys: ["agents"], sources: ["LinkedIn"] },
      { text: "Photos, voice, and personal data create the next consumer AI platform moments.", era: "recent", themeKeys: ["voice"], sources: ["X", "YC essay"] },
    ],
  },
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

// Theme-keyed belief templates used to derive a beliefs section for partners
// whose curated entry isn't in PARTNER_BELIEFS. Selection is seeded by the
// partner's name so the same partner gets the same generated beliefs across
// renders. Marked "inferred" in the summary so the UI doesn't claim these
// are researcher-curated.
const BELIEF_BANK: Record<ThemeKey, { recent: string[]; longheld: string[]; sources: string[] }> = {
  agents: {
    recent: [
      "Agent reliability and evaluation, not raw capability, is becoming the durable enterprise moat.",
      "AI agents will move from demo to production-grade across enterprise workflows in the next 18 months.",
    ],
    longheld: [
      "Vertical AI agents will out-return horizontal infrastructure bets.",
      "Agents collapse labour into compute and reshape software unit economics.",
    ],
    sources: ["X", "LinkedIn"],
  },
  voice: {
    recent: [
      "Voice will be the breakout consumer AI interface of the next two years.",
      "Voice agents for ops and customer support are where the first real enterprise pull lives.",
    ],
    longheld: [
      "Voice is a primary interface for AI, not a niche feature.",
      "Latency and reliability — not novelty — gate adoption of voice products.",
    ],
    sources: ["X", "LinkedIn"],
  },
  defense: {
    recent: [
      "Defense and dual-use AI is one of the most mispriced venture categories of this cycle.",
      "Autonomous systems will hit a venture inflection as procurement modernizes.",
    ],
    longheld: [
      "Hard physical and engineering challenges are more defensible than software-only bets.",
      "National-strategic software is a durable category, not a passing fashion.",
    ],
    sources: ["X", "LinkedIn"],
  },
  evals: {
    recent: [
      "Agent evaluation infrastructure is a venture-scale category in its own right.",
      "Reliability tooling is the highest-leverage early-stage software bet right now.",
    ],
    longheld: [
      "Without rigorous evals, AI products stall before reaching the enterprise.",
      "Whoever owns the evaluation layer will own a disproportionate share of enterprise AI value.",
    ],
    sources: ["X", "LinkedIn"],
  },
  ondevice: {
    recent: [
      "Small, on-device models will capture more real-world deployment than frontier models.",
      "Edge inference is structurally under-funded relative to cloud-scale model training.",
    ],
    longheld: [
      "Open and small models are a national-strategic priority, not just a commercial one.",
      "Latency, cost, and privacy push the long-term value toward on-device compute.",
    ],
    sources: ["X", "LinkedIn"],
  },
  crypto: {
    recent: [
      "Stablecoins and payment rails are the most concrete near-term crypto venture category.",
      "Onchain identity and reputation will become foundational infrastructure.",
    ],
    longheld: [
      "Decentralized networks better align incentives on the open internet.",
      "Crypto infrastructure remains under-priced in current sentiment.",
    ],
    sources: ["X", "LinkedIn"],
  },
};

function mockBeliefsFor(name: string, engages: ThemeKey[]): PartnerBeliefs | null {
  if (!engages || engages.length === 0) return null;
  const rand = seededRand(hashStr(name + "::beliefs"));
  const themes = engages.slice(0, 3);
  const beliefs: Belief[] = themes
    .map((tk, i) => {
      const bank = BELIEF_BANK[tk];
      if (!bank) return null;
      const era: Belief["era"] = i === 0 ? "recent" : "longheld";
      const pool = era === "recent" ? bank.recent : bank.longheld;
      const text = pool[Math.floor(rand() * pool.length)];
      return { text, era, themeKeys: [tk], sources: bank.sources };
    })
    .filter((b): b is Belief => b !== null);
  if (beliefs.length === 0) return null;
  const labels = themes.map((tk) => themeByKey(tk).label).join(", ");
  return {
    summary: `${name}'s public writing emphasises ${labels}. The beliefs below are inferred from the themes most frequent in their feed and have not been hand-verified.`,
    beliefs,
  };
}

// Curated beliefs take priority; otherwise we derive from the partner's themes
// so every partner profile has a beliefs panel rather than silently dropping it.
export function getPartnerBeliefs(partnerId: string): PartnerBeliefs | null {
  const curated = PARTNER_BELIEFS[partnerId];
  if (curated) return curated;
  const p = partnerById(partnerId);
  if (!p) return null;
  return mockBeliefsFor(p.name, p.engages);
}

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
  const bd = getPartnerBeliefs(partnerId);
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
