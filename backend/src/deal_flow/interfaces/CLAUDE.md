# Interfaces layer — Interface Adapters

Translates between the outside world (HTTP, CLI, etc.) and the use cases. Controllers and presenters live here.

## Allowed imports
- `deal_flow.domain.*`, `deal_flow.application.*`
- `deal_flow.infrastructure.*` — **only** inside the composition root (`api/dependencies.py`)
- `fastapi`, `pydantic` — only in this layer

## Forbidden
- Business logic. If you're writing `if`/`else` on domain concepts here, it belongs in a use case.
- Importing infrastructure outside the composition root (route handlers receive ports via `Depends`, not by importing concrete adapters)

## Structure
- `api/app.py` — FastAPI instance, router includes, lifespan
- `api/routes/` — one file per resource. Routes are thin: parse → call use case → present.
- `api/schemas/` — Pydantic request/response models. Convert to/from application DTOs at the boundary.
- `api/dependencies.py` — **composition root**. The one place where concrete infrastructure adapters are wired to application ports.
- `cli/` — Click/Typer command entrypoints (same shape: parse → use case → present)
- `presenters/` — format use-case output for a specific delivery mechanism (JSON, plaintext, etc.)

## Pattern
```python
# api/routes/deals.py
@router.get("/firms/{firm_id}/deals")
def list_deals(firm_id: str, use_case: FindDeals = Depends(get_find_deals)) -> list[DealResponse]:
    deals = use_case.execute(FindDealsInput(firm_id=firm_id))
    return [DealResponse.from_domain(d) for d in deals]
```
