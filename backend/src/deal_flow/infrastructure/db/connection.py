"""Postgres connection plumbing.

Each FastAPI request gets its own short-lived psycopg connection through
`get_connection`. Neon's pooled `DATABASE_URL` handles the per-request fanout
that's typical of serverless deploys (Vercel) — we don't run our own pool.
"""

from __future__ import annotations

from collections.abc import Iterator

import psycopg

from deal_flow.infrastructure.config.settings import get_settings


def get_connection() -> Iterator[psycopg.Connection]:
    """FastAPI dependency: yield a connection, close on request teardown."""
    settings = get_settings()
    conn = psycopg.connect(settings.database_url)
    try:
        yield conn
    finally:
        conn.close()
