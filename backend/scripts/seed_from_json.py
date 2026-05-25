"""One-time loader: copies the contents of backend/data/*.json into Postgres.

Idempotent — uses INSERT ... ON CONFLICT DO UPDATE so re-runs converge on the
current JSON. Per firm:
  - partners table: keyed by (firm_domain, profile_url)
  - portfolio_companies table: keyed by (firm_domain, detail_url)
  - portfolio_founders: deleted-then-reinserted per company (ordering matters)

Invoke from the backend/ directory:
    python scripts/seed_from_json.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import psycopg

from deal_flow.infrastructure.config.settings import get_settings
from deal_flow.infrastructure.persistence.file_partner_profile_repository import (
    _normalize_photo_url,
)

# firm_domain → slug used in backend/data/{slug}_partners.json + {slug}_portfolio.json.
# Same map as in file_partner_profile_repository.py / file_portfolio_company_repository.py.
FIRMS: dict[str, str] = {
    "a16z.com": "a16z",
    "sequoiacap.com": "sequoia",
    "ycombinator.com": "ycombinator",
}


def _str(value: object) -> str | None:
    if value is None:
        return None
    s = str(value)
    return s if s != "" else None


def _str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v) for v in value if v not in (None, "")]


def _partner_row(firm_domain: str, raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "firm_domain": firm_domain,
        "name": str(raw.get("name") or ""),
        "profile_url": str(raw.get("profile_url") or ""),
        "role": _str(raw.get("role")),
        "role_display": _str(raw.get("role_display")),
        "focus_areas": _str_list(raw.get("focus_areas")),
        "teams": _str_list(raw.get("teams")),
        "bio": _str(raw.get("bio")),
        "about_short": _str(raw.get("about_short")),
        "linkedin_url": _str(raw.get("linkedin_url")),
        "x_url": _str(raw.get("x_url")),
        "farcaster_url": _str(raw.get("farcaster_url")),
        "email": _str(raw.get("email")),
        "photo_url": _normalize_photo_url(raw.get("photo_url")),
        "education": _str_list(raw.get("education")),
        "prior_experience": _str_list(raw.get("prior_experience")),
    }


def _company_row(firm_domain: str, raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "firm_domain": firm_domain,
        "name": str(raw.get("name") or ""),
        "detail_url": str(raw.get("detail_url") or ""),
        "website": _str(raw.get("website")),
        "sector": _str(raw.get("sector")),
        "description": _str(raw.get("description")),
        "linkedin_url": _str(raw.get("linkedin_url")),
        "photo_url": _str(raw.get("photo_url")),
    }


def _founder_rows(company_id: int, raw_founders: object) -> list[tuple[int, int, str, str | None]]:
    if not isinstance(raw_founders, list):
        return []
    out: list[tuple[int, int, str, str | None]] = []
    for position, f in enumerate(raw_founders):
        if not isinstance(f, dict):
            continue
        out.append(
            (
                company_id,
                position,
                str(f.get("name") or ""),
                _str(f.get("role")),
            )
        )
    return out


def _upsert_partners(conn: psycopg.Connection, firm_domain: str, items: list[dict]) -> int:
    sql = """
        INSERT INTO partners (
            firm_domain, name, profile_url, role, role_display,
            focus_areas, teams, bio, about_short,
            linkedin_url, x_url, farcaster_url, email, photo_url,
            education, prior_experience
        ) VALUES (
            %(firm_domain)s, %(name)s, %(profile_url)s, %(role)s, %(role_display)s,
            %(focus_areas)s, %(teams)s, %(bio)s, %(about_short)s,
            %(linkedin_url)s, %(x_url)s, %(farcaster_url)s, %(email)s, %(photo_url)s,
            %(education)s, %(prior_experience)s
        )
        ON CONFLICT (firm_domain, profile_url) DO UPDATE SET
            name = EXCLUDED.name,
            role = EXCLUDED.role,
            role_display = EXCLUDED.role_display,
            focus_areas = EXCLUDED.focus_areas,
            teams = EXCLUDED.teams,
            bio = EXCLUDED.bio,
            about_short = EXCLUDED.about_short,
            linkedin_url = EXCLUDED.linkedin_url,
            x_url = EXCLUDED.x_url,
            farcaster_url = EXCLUDED.farcaster_url,
            email = EXCLUDED.email,
            photo_url = EXCLUDED.photo_url,
            education = EXCLUDED.education,
            prior_experience = EXCLUDED.prior_experience
    """
    count = 0
    for item in items:
        if not item.get("profile_url"):
            continue
        conn.execute(sql, _partner_row(firm_domain, item))
        count += 1
    return count


def _upsert_companies(conn: psycopg.Connection, firm_domain: str, items: list[dict]) -> int:
    upsert_sql = """
        INSERT INTO portfolio_companies (
            firm_domain, name, detail_url, website, sector,
            description, linkedin_url, photo_url
        ) VALUES (
            %(firm_domain)s, %(name)s, %(detail_url)s, %(website)s, %(sector)s,
            %(description)s, %(linkedin_url)s, %(photo_url)s
        )
        ON CONFLICT (firm_domain, detail_url) DO UPDATE SET
            name = EXCLUDED.name,
            website = EXCLUDED.website,
            sector = EXCLUDED.sector,
            description = EXCLUDED.description,
            linkedin_url = EXCLUDED.linkedin_url,
            photo_url = EXCLUDED.photo_url
        RETURNING id
    """
    delete_founders_sql = "DELETE FROM portfolio_founders WHERE company_id = %s"
    insert_founder_sql = (
        "INSERT INTO portfolio_founders (company_id, position, name, role) "
        "VALUES (%s, %s, %s, %s)"
    )

    count = 0
    for item in items:
        if not item.get("detail_url"):
            continue
        row = _company_row(firm_domain, item)
        company_id = conn.execute(upsert_sql, row).fetchone()[0]
        conn.execute(delete_founders_sql, (company_id,))
        founders = _founder_rows(company_id, item.get("founders"))
        if founders:
            conn.cursor().executemany(insert_founder_sql, founders)
        count += 1
    return count


def _load_partners_json(data_dir: Path, slug: str) -> list[dict]:
    path = data_dir / f"{slug}_partners.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw.get("partners") or []


def _load_portfolio_json(data_dir: Path, slug: str) -> list[dict]:
    path = data_dir / f"{slug}_portfolio.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw.get("companies") or []


def main() -> int:
    settings = get_settings()
    if not settings.database_url:
        print("DATABASE_URL is empty. Set it in backend/.env first.", file=sys.stderr)
        return 1

    data_dir = settings.partner_data_dir
    print(f"Reading JSON from {data_dir}")
    print(f"Connecting to {settings.database_url.split('@')[-1].split('/')[0]}")

    with psycopg.connect(settings.database_url, autocommit=False) as conn:
        for firm_domain, slug in FIRMS.items():
            partners = _load_partners_json(data_dir, slug)
            companies = _load_portfolio_json(data_dir, slug)

            with conn.transaction():
                p_count = _upsert_partners(conn, firm_domain, partners)
                c_count = _upsert_companies(conn, firm_domain, companies)

            f_count = conn.execute(
                """
                SELECT COUNT(*) FROM portfolio_founders pf
                JOIN portfolio_companies pc ON pc.id = pf.company_id
                WHERE pc.firm_domain = %s
                """,
                (firm_domain,),
            ).fetchone()[0]

            print(
                f"  {firm_domain}: "
                f"partners JSON={len(partners)} → DB upserted={p_count}; "
                f"portfolio JSON={len(companies)} → DB upserted={c_count}; "
                f"founders rows={f_count}"
            )

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
