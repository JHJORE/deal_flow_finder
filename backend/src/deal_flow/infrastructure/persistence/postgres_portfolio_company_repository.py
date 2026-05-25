"""Postgres-backed `PortfolioCompanyRepository`. Returns the same
`PortfolioCompany` shape as `FilePortfolioCompanyRepository`. Founders are
ordered by `portfolio_founders.position` (the original JSON ordering).
"""

from __future__ import annotations

from collections import defaultdict

import psycopg

from deal_flow.application.ports.repositories.portfolio_company_repository import (
    PortfolioCompanyRepository,
)
from deal_flow.domain.entities.founder import Founder
from deal_flow.domain.entities.portfolio_company import PortfolioCompany

_SELECT_COMPANIES = """
    SELECT id, name, detail_url, website, sector,
           description, linkedin_url, photo_url
    FROM portfolio_companies
    WHERE firm_domain = %s
    ORDER BY id
"""

_SELECT_FOUNDERS_FOR_IDS = """
    SELECT company_id, position, name, role
    FROM portfolio_founders
    WHERE company_id = ANY(%s)
    ORDER BY company_id, position
"""


class PostgresPortfolioCompanyRepository(PortfolioCompanyRepository):
    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def list_by_firm(self, firm_domain: str) -> list[PortfolioCompany]:
        company_rows = self._conn.execute(_SELECT_COMPANIES, (firm_domain,)).fetchall()
        if not company_rows:
            return []

        ids = [r[0] for r in company_rows]
        founders_by_company: dict[int, list[Founder]] = defaultdict(list)
        for cid, _pos, fname, frole in self._conn.execute(
            _SELECT_FOUNDERS_FOR_IDS, (ids,)
        ).fetchall():
            founders_by_company[cid].append(Founder(name=fname or "", role=frole))

        return [
            PortfolioCompany(
                name=name or "",
                detail_url=detail_url or "",
                website=website,
                sector=sector,
                description=description,
                linkedin_url=linkedin_url,
                photo_url=photo_url,
                founders=tuple(founders_by_company.get(cid, ())),
            )
            for cid, name, detail_url, website, sector, description, linkedin_url, photo_url in company_rows
        ]
