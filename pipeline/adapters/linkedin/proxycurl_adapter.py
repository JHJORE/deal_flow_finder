"""Proxycurl adapter for the ``LinkedInFetcher`` port.

Proxycurl calls are expensive (a few cents each), so every response is
cached on disk under ``data/linkedin/_cache/`` keyed by URL hash. The cache
is checked before any network call. Cache invalidation is manual — delete
the file or the directory.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import httpx

from pipeline.adapters._common.http import request_with_retry
from pipeline.entities.errors import ParseError, ValidationError
from pipeline.entities.models import LinkedInCompany, LinkedInProfile
from pipeline.entities.value_objects import Timestamp, Url

PROFILE_ENDPOINT = "https://nubela.co/proxycurl/api/v2/linkedin"
COMPANY_ENDPOINT = "https://nubela.co/proxycurl/api/linkedin/company"


class ProxycurlLinkedInFetcher:
    def __init__(self, client: httpx.Client, cache_dir: Path) -> None:
        self._client = client
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_profile(self, linkedin_url: Url) -> LinkedInProfile | None:
        payload = self._fetch_cached("profile", linkedin_url, PROFILE_ENDPOINT)
        if payload is None:
            return None
        try:
            current = (payload.get("experiences") or [{}])[0]
            return LinkedInProfile(
                linkedin_url=linkedin_url,
                captured_at=Timestamp.now(),
                current_title=str(current.get("title", "")),
                current_company=str(current.get("company", "")),
                headline=str(payload.get("headline", "")),
                recent_role_change=False,
            )
        except (TypeError, ValueError, ValidationError) as exc:
            raise ParseError(
                f"could not parse proxycurl profile for {linkedin_url}: {exc}"
            ) from exc

    def fetch_company(self, linkedin_url: Url) -> LinkedInCompany | None:
        payload = self._fetch_cached("company", linkedin_url, COMPANY_ENDPOINT)
        if payload is None:
            return None
        try:
            return LinkedInCompany(
                linkedin_url=linkedin_url,
                captured_at=Timestamp.now(),
                name=str(payload.get("name", "")),
                headcount=_maybe_int(payload.get("company_size_on_linkedin")),
                recent_senior_hires=(),  # Proxycurl doesn't expose this directly.
            )
        except (TypeError, ValueError, ValidationError) as exc:
            raise ParseError(
                f"could not parse proxycurl company for {linkedin_url}: {exc}"
            ) from exc

    # ------------------------------------------------------------------ #

    def _fetch_cached(self, kind: str, url: Url, endpoint: str) -> dict[str, Any] | None:
        cache_path = self._cache_path(kind, url)
        if cache_path.exists():
            with cache_path.open("r", encoding="utf-8") as fh:
                cached = json.load(fh)
            return cached if isinstance(cached, dict) else None

        resp = request_with_retry(lambda: self._client.get(endpoint, params={"url": url.value}))
        if resp.status_code == 404:
            return None
        try:
            payload = resp.json()
        except ValueError as exc:
            raise ParseError(f"proxycurl returned non-json: {exc}") from exc
        if not isinstance(payload, dict):
            raise ParseError(f"proxycurl returned non-object: {type(payload).__name__}")

        with cache_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        return payload

    def _cache_path(self, kind: str, url: Url) -> Path:
        digest = hashlib.sha256(url.value.encode("utf-8")).hexdigest()[:16]
        return self._cache_dir / f"{kind}_{digest}.json"


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
