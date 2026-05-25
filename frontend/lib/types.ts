export type FirmId = "sequoia" | "a16z" | "yc";

export type Firm = {
  id: FirmId;
  name: string;
};

export type ThemeKey =
  | "agents"
  | "voice"
  | "defense"
  | "evals"
  | "ondevice"
  | "crypto";

export type Theme = {
  key: ThemeKey;
  label: string;
  hue: number; // OKLCH hue used for chart strokes
  chroma?: number;
  share: number[];
  age: string;
  trend: "rising" | "cooling";
};

export type TopicRow = {
  t: string;
  w: number;
  chg: number;
  isNew: boolean;
  themeKey?: ThemeKey | null;
};

export type Contact = {
  email: string;
  founderEmail?: string;
  phone: string;
  linkedin: string;
  x: string;
  site?: string;
};

export type PartnerStage = "early" | "growth" | "both";

export type Partner = {
  id: string;
  name: string;
  firm: FirmId;
  role: string;
  focus: string;
  stage?: PartnerStage;
  photoUrl: string | null;
  posts: number[];
  engageRate: number[];
  spike: boolean;
  engages: ThemeKey[];
  newTopic: string | null;
  topics: TopicRow[];
  // derived
  contact: Contact;
  about: string;
  checkSize: string;
};

export type Founder = {
  id: string;
  name: string;
  handle: string;
  role: string;
  engages: ThemeKey[];
  posts: number[];
  engageRate: number[];
  followerGrowth: string;
  topics: TopicRow[];
};

export type Deal = {
  partner: string;
  round: string;
  invested: string;
  ownership: string;
  valuation: string;
  dealDate: string;
  lead: boolean;
};

export type SeniorHire = {
  role: string;
  name: string;
  hot: boolean;
};

export type CompanyFounder = {
  name: string;
  role: string | null;
};

export type Company = {
  id: string;
  name: string;
  firm: FirmId;
  founder: string;            // first founder name from JSON (legacy convenience)
  foundersList: CompanyFounder[]; // full founders list with roles, from JSON
  sector: string;             // raw sector string from JSON (may contain "A, B, C")
  description: string | null; // raw description from JSON (may be null)
  detailUrl: string;          // link to the firm's portfolio page for this company
  website: string | null;     // raw website URL from JSON
  linkedinUrl: string | null; // raw LinkedIn URL from JSON
  photoUrl?: string | null;   // logo URL from JSON
  // The fields below have no source in the portfolio JSON. They are kept on
  // the type so legacy consumers (CompanyProfileView modal, WatchlistView,
  // ConsensusView) keep compiling, but for JSON-derived companies they are
  // empty/zero. Views should treat them as "no data available".
  stage: string;
  founderTracked: string | null;
  themeKeys: ThemeKey[];
  deal: Deal;
  jobs: number[];
  seniorHires: SeniorHire[];
  note: string;
  contact: Contact;
  about: string;
  topics?: TopicRow[];
};

export type Signal = {
  id: string;
  tier: 1 | 2 | 3 | 4;
  conf: "high" | "med" | "low";
  firms: FirmId[];
  headline: string;
  body: string;
  sources: string[];
  actors: string[];
  age: string;
  score: number;
  filing?: string;
};

export type Filing = {
  issuer: string;
  relatedFounder: string | null;
  relatedCompany: string | null;
  formType: string;
  filedDate: string;
  cik: string;
  exemption: string;
  offeringAmount: string;
  soldToDate: string;
  totalInvestors: number;
  firstSale: string;
  industry: string;
  state: string;
  namedInvestor: string;
  relatedPersons: string[];
  edgarUrl: string;
  whyFlagged: string;
  timeline: { d: string; t: string; s: string }[];
};

export type Follow = {
  partner: string;
  founder: string;
  firstSeen: number;
};

export type Belief = {
  text: string;
  era: "recent" | "longheld";
  themeKeys: ThemeKey[];
  sources: string[];
};

export type PartnerBeliefs = {
  summary: string;
  beliefs: Belief[];
};

export type TopPost = {
  text: string;
  when: string;
  likes: string;
  reposts: string;
};

export type EntityKind = "partner" | "company" | "filing";

export type OpenEntity = {
  kind: EntityKind;
  id: string;
} | null;

export type ViewId =
  | "signals"
  | "people"
  | "portfolio"
  | "consensus"
  | "graph"
  | "watchlist";
