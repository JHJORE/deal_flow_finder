"""Construct a real Firecrawl SDK client. The only place ``firecrawl_py`` is imported."""

from __future__ import annotations

import os
from typing import Any


def build_firecrawl_client() -> Any:
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        raise RuntimeError("FIRECRAWL_API_KEY is not set in the environment")
    from firecrawl import FirecrawlApp  # local import keeps the module light at import time

    return FirecrawlApp(api_key=api_key)
