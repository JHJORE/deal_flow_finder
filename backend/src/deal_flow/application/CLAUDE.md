# Application layer — Use Cases

Application-specific business rules. Orchestrates entities to fulfill a single user-facing operation (e.g. "find deals for firm X", "ingest filing Y").

## Allowed imports
- `deal_flow.domain.*`
- Python stdlib + `abc` for defining ports

## Forbidden imports
- `deal_flow.interfaces`, `deal_flow.infrastructure` — never
- No `fastapi`, no `sqlalchemy`, no HTTP clients, no env reading
- No concrete I/O — talk to the outside world only through **ports** defined here

## Structure
- `use_cases/` — one class per use case. Constructor takes ports it needs. One public method (`execute`, `__call__`, etc.).
- `ports/repositories/` — ABCs the use cases depend on for persistence (e.g. `DealRepository`)
- `ports/services/` — ABCs for external services (e.g. `FilingFetcher`, `EmailSender`)
- `dtos/` — plain data structures that cross the boundary (input/output of use cases). Use `@dataclass(frozen=True)`, not Pydantic.

## Pattern
```python
# application/use_cases/find_deals.py
from dataclasses import dataclass
from deal_flow.application.ports.repositories.deal_repository import DealRepository

@dataclass(frozen=True)
class FindDealsInput:
    firm_id: str

class FindDeals:
    def __init__(self, deals: DealRepository) -> None:
        self._deals = deals

    def execute(self, input: FindDealsInput) -> list[Deal]:
        return self._deals.list_for_firm(input.firm_id)
```

The use case never instantiates `DealRepository` — it receives one. Wiring happens in `interfaces/api/dependencies.py`.
