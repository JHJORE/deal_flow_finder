"""Construct an Anthropic Claude client. The only place ``anthropic`` is imported."""

from __future__ import annotations

import os
from typing import Any


def build_anthropic_client() -> Any:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set in the environment")
    from anthropic import Anthropic

    return Anthropic(api_key=api_key)
