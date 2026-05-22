# Backend

Python Clean Architecture. See `CLAUDE.md` for the layer rules.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
uvicorn deal_flow.interfaces.api.app:app --reload
# → http://127.0.0.1:8000/health
```

## Test

```bash
pytest
```

## Lint

```bash
ruff check .
```
