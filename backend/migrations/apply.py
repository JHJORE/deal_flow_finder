"""Tiny migration runner. Applies every NNN_*.sql file in this directory that
isn't already recorded in the schema_migrations table. Idempotent.

Invoke from the backend/ directory:
    python -m migrations.apply
"""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg

from deal_flow.infrastructure.config.settings import get_settings

MIGRATIONS_DIR = Path(__file__).resolve().parent


def _ensure_table(conn: psycopg.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version    TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def _applied_versions(conn: psycopg.Connection) -> set[str]:
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row[0] for row in rows}


def _pending(applied: set[str]) -> list[Path]:
    files = sorted(p for p in MIGRATIONS_DIR.glob("*.sql"))
    return [p for p in files if p.stem not in applied]


def main() -> int:
    settings = get_settings()
    if not settings.database_url:
        print("DATABASE_URL is empty. Set it in backend/.env first.", file=sys.stderr)
        return 1

    with psycopg.connect(settings.database_url, autocommit=False) as conn:
        _ensure_table(conn)
        conn.commit()

        applied = _applied_versions(conn)
        pending = _pending(applied)

        if not pending:
            print("No pending migrations.")
            return 0

        for path in pending:
            version = path.stem
            print(f"Applying {version} ...")
            sql = path.read_text(encoding="utf-8")
            with conn.transaction():
                conn.execute(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)",
                    (version,),
                )
            print(f"  applied {version}")

    print(f"Applied {len(pending)} migration(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
