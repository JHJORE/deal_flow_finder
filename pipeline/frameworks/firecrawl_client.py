"""Construct a real Firecrawl v2 SDK client. The only place ``firecrawl`` is imported."""

from __future__ import annotations

import os
from typing import Any


def build_firecrawl_client() -> Any:
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        raise RuntimeError("FIRECRAWL_API_KEY is not set in the environment")
    from firecrawl import Firecrawl  # local import keeps the module light at import time

    return Firecrawl(api_key=api_key)
