# Infrastructure layer — Frameworks & Drivers

The outermost ring. All concrete I/O lives here: databases, HTTP clients, file system, env vars, third-party SDKs.

## Allowed imports
- `deal_flow.domain.*`, `deal_flow.application.*` (to implement the ports defined there)
- Any third-party package — this is the only layer that touches the outside world

## Forbidden
- Being imported by `domain` or `application` — they only depend on the **ports** (ABCs) defined in `application`. You implement those ports here.
- Leaking infrastructure types upward. A repository implementation returns domain entities, not ORM rows.

## Structure
- `persistence/` — concrete repository implementations (e.g. `PostgresDealRepository(DealRepository)`)
- `external/` — third-party API clients (e.g. EDGAR, Firecrawl). Each implements a port from `application/ports/services/`.
- `config/settings.py` — env loading via `pydantic-settings`. The only file that reads `os.environ` directly.

## Pattern
```python
# infrastructure/persistence/postgres_deal_repository.py
from deal_flow.application.ports.repositories.deal_repository import DealRepository
from deal_flow.domain.entities.deal import Deal

class PostgresDealRepository(DealRepository):
    def __init__(self, conn) -> None:
        self._conn = conn

    def list_for_firm(self, firm_id: str) -> list[Deal]:
        rows = self._conn.execute(...).fetchall()
        return [Deal(...) for row in rows]  # map row → domain entity
```

The use case sees `DealRepository`; it doesn't know Postgres exists.
