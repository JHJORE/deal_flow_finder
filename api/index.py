"""Vercel Python serverless entrypoint.

Vercel discovers `api/*.py` files and serves them as serverless functions.
This module re-exports the FastAPI app so all `/api/*` requests are handled
by the backend's HTTP layer (see `backend/src/deal_flow/interfaces/api/app.py`).

The `vercel.json` rewrite sends every `/api/(.*)` request here.
"""

import sys
from pathlib import Path

# Make the backend's src/ importable when Vercel builds this function.
_BACKEND_SRC = Path(__file__).resolve().parent.parent / "backend" / "src"
if str(_BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(_BACKEND_SRC))

from deal_flow.interfaces.api.app import app  # noqa: E402, F401
