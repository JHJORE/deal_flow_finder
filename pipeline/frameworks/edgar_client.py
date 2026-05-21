"""Construct an httpx.Client for SEC EDGAR.

SEC requires a User-Agent header identifying the requester. Without one,
requests are throttled or rejected outright.
"""

from __future__ import annotations

import os

import httpx


def build_edgar_client() -> httpx.Client:
    user_agent = os.environ.get("EDGAR_USER_AGENT")
    if not user_agent:
        raise RuntimeError("EDGAR_USER_AGENT is not set; SEC requires a 'Name email' identifier")
    return httpx.Client(
        headers={"User-Agent": user_agent, "Accept": "application/json"},
        timeout=httpx.Timeout(30.0),
    )
