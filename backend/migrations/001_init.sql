-- Initial schema for partner + portfolio data lifted from backend/data/*.json.
-- Tables mirror domain entities in src/deal_flow/domain/entities/ field-by-field.
-- firm_domain values: 'a16z.com', 'sequoiacap.com', 'ycombinator.com'.

CREATE TABLE partners (
  id                BIGSERIAL PRIMARY KEY,
  firm_domain       TEXT NOT NULL,
  name              TEXT NOT NULL,
  profile_url       TEXT NOT NULL,
  role              TEXT,
  role_display      TEXT,
  focus_areas       TEXT[] NOT NULL DEFAULT '{}',
  teams             TEXT[] NOT NULL DEFAULT '{}',
  bio               TEXT,
  about_short       TEXT,
  linkedin_url      TEXT,
  x_url             TEXT,
  farcaster_url     TEXT,
  email             TEXT,
  photo_url         TEXT,
  education         TEXT[] NOT NULL DEFAULT '{}',
  prior_experience  TEXT[] NOT NULL DEFAULT '{}',
  UNIQUE (firm_domain, profile_url)
);
CREATE INDEX partners_firm_domain_idx ON partners (firm_domain);

CREATE TABLE portfolio_companies (
  id            BIGSERIAL PRIMARY KEY,
  firm_domain   TEXT NOT NULL,
  name          TEXT NOT NULL,
  detail_url    TEXT NOT NULL,
  website       TEXT,
  sector        TEXT,
  description   TEXT,
  linkedin_url  TEXT,
  photo_url     TEXT,
  UNIQUE (firm_domain, detail_url)
);
CREATE INDEX portfolio_companies_firm_domain_idx ON portfolio_companies (firm_domain);

CREATE TABLE portfolio_founders (
  company_id  BIGINT NOT NULL REFERENCES portfolio_companies(id) ON DELETE CASCADE,
  position    INT    NOT NULL,
  name        TEXT   NOT NULL,
  role        TEXT,
  PRIMARY KEY (company_id, position)
);
