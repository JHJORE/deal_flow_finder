"""Construct a configured httpx.Client for Proxycurl."""

from __future__ import annotations

import os

import httpx


def build_proxycurl_client() -> httpx.Client:
    api_key = os.environ.get("PROXYCURL_API_KEY")
    if not api_key:
        raise RuntimeError("PROXYCURL_API_KEY is not set in the environment")
    return httpx.Client(
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        timeout=httpx.Timeout(60.0),
    )
