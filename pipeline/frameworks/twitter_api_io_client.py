"""Construct a configured httpx.Client for twitterapi.io."""

from __future__ import annotations

import os

import httpx


def build_twitter_api_io_client() -> httpx.Client:
    api_key = os.environ.get("TWITTERAPI_IO_KEY")
    if not api_key:
        raise RuntimeError("TWITTERAPI_IO_KEY is not set in the environment")
    return httpx.Client(
        headers={"X-API-Key": api_key, "Accept": "application/json"},
        timeout=httpx.Timeout(30.0),
    )
