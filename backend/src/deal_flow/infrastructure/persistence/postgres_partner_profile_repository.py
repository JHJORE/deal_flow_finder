"""Postgres-backed `PartnerProfileRepository`. Returns the same `Partner`
shape as `FilePartnerProfileRepository` so the API response is unchanged when
the wiring is flipped — including dropping `farcaster_url` (the file mapper
doesn't set it; we mirror that here for a byte-identical response).
"""

from __future__ import annotations

import psycopg

from deal_flow.application.ports.repositories.partner_profile_repository import (
    PartnerProfileRepository,
)
from deal_flow.domain.entities.partner import Partner

_SELECT = """
    SELECT name, profile_url, role, role_display,
           focus_areas, teams, bio, about_short,
           linkedin_url, x_url, email, photo_url,
           education, prior_experience
    FROM partners
    WHERE firm_domain = %s
    ORDER BY id
"""


class PostgresPartnerProfileRepository(PartnerProfileRepository):
    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def list_by_firm(self, firm_domain: str) -> list[Partner]:
        rows = self._conn.execute(_SELECT, (firm_domain,)).fetchall()
        return [_row_to_partner(r) for r in rows]


def _row_to_partner(r: tuple) -> Partner:
    (
        name, profile_url, role, role_display,
        focus_areas, teams, bio, about_short,
        linkedin_url, x_url, email, photo_url,
        education, prior_experience,
    ) = r
    return Partner(
        name=name or "",
        profile_url=profile_url or "",
        role=role,
        role_display=role_display,
        focus_areas=tuple(focus_areas or ()),
        teams=tuple(teams or ()),
        bio=bio,
        about_short=about_short,
        linkedin_url=linkedin_url,
        x_url=x_url,
        email=email,
        photo_url=photo_url,
        education=tuple(education or ()),
        prior_experience=tuple(prior_experience or ()),
    )
