# Domain layer — Entities

The **innermost** ring of Clean Architecture. Pure business objects. Knows nothing about the outside world.

## Allowed imports
- Python stdlib only (`dataclasses`, `enum`, `datetime`, `decimal`, `typing`, etc.)
- Other modules **inside** `deal_flow.domain.*`

## Forbidden imports
- `deal_flow.application`, `deal_flow.interfaces`, `deal_flow.infrastructure` — never
- Any third-party package: no `pydantic`, no `sqlalchemy`, no `fastapi`, no `requests`, no ORMs, no HTTP clients, no env reading
- No I/O of any kind — no file, network, DB, or clock reads (pass `now` in as a parameter if you need it)

## What lives here
- `entities/` — objects with identity that change over time (e.g. a `Deal`, a `Firm`)
- `value_objects/` — immutable, identity-less values (e.g. `Money`, `Cusip`, `Ticker`)
- Domain exceptions (e.g. `InvalidDealState`)

## Rule of thumb
If you can't unit-test this code with zero mocks and zero fixtures, it doesn't belong here. The domain is the part of the system that would still make sense if you ripped out the web, the DB, and every external API.
