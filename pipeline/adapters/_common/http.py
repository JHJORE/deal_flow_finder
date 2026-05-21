"""Shared HTTP helpers for adapters.

Single retry with exponential backoff on rate-limit responses, per the spec.
Everything else is left to the caller — adapters know the shape of their
own APIs better than a generic wrapper would.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

import httpx

from pipeline.entities.errors import FetchError, RateLimitError

T = TypeVar("T")


def request_with_retry(
    call: Callable[[], httpx.Response],
    *,
    backoff_seconds: float = 2.0,
) -> httpx.Response:
    """Run ``call`` once; on 429, sleep ``backoff_seconds`` and retry once more.

    Raises:
        RateLimitError: if the retry also returns 429.
        FetchError: for any other non-2xx response or network failure.
    """
    try:
        response = call()
    except httpx.HTTPError as exc:
        raise FetchError(f"network failure: {exc}") from exc

    if response.status_code == 429:
        retry_after = _retry_after_seconds(response, default=backoff_seconds)
        time.sleep(retry_after)
        try:
            response = call()
        except httpx.HTTPError as exc:
            raise FetchError(f"network failure on retry: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitError("rate limit persisted after single retry")

    if response.status_code >= 500:
        raise FetchError(f"upstream {response.status_code}: {response.text[:200]}")
    if response.status_code >= 400 and response.status_code != 404:
        raise FetchError(f"client error {response.status_code}: {response.text[:200]}")

    return response


def _retry_after_seconds(response: httpx.Response, default: float) -> float:
    header = response.headers.get("retry-after")
    if header is None:
        return default
    try:
        return max(float(header), default)
    except ValueError:
        return default
