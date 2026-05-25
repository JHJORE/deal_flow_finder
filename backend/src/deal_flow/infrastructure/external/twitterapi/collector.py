from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

from deal_flow.application.ports.services.twitter_collector import TwitterCollector
from deal_flow.infrastructure.cache.file_cache import FileCache


class TwitterApiError(RuntimeError):
    """Raised when twitterapi.io returns a non-2xx response.

    Carries the raw response body so failures stay debuggable; we never paper
    over them with retries or default values.
    """


class TwitterApiCollector(TwitterCollector):
    """The single twitterapi.io adapter.

    Read-only by construction: only GET endpoints, no ``v2`` paths, no login,
    no write actions. Owns the on-disk SHA256 cache; each port-method call is
    a single cache entry covering the entire paginated result (so changing the
    cap invalidates the cache).
    """

    BASE_URL = "https://api.twitterapi.io"

    def __init__(self, api_key: str, cache_dir: Path, refresh: bool = False) -> None:
        if not api_key:
            raise ValueError("TWITTERAPI_KEY is not set")
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers={"X-API-Key": api_key},
            timeout=30.0,
        )
        self._cache = FileCache(cache_dir)
        self._refresh = refresh

    # ---- caching wrapper (identical shape to FirecrawlExtractor._cached) ----

    def _cached(
        self,
        op: str,
        key_inputs: dict[str, Any],
        fetch: Callable[[], tuple[Any, Any]],
    ) -> Any:
        key = FileCache.key_for(op, **key_inputs)
        if not self._refresh:
            hit = self._cache.read(key)
            if hit is not None:
                return hit["payload"]
        payload, _raw = fetch()
        self._cache.write(
            key, {"op": op, "inputs": key_inputs, "payload": payload}
        )
        return payload

    # ---- HTTP primitive ----

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        resp = self._client.get(path, params=params)
        if resp.status_code >= 400:
            raise TwitterApiError(
                f"GET {path} → {resp.status_code}: {resp.text[:500]}"
            )
        return resp.json()

    # ---- pagination loop ----

    def _paginate(
        self,
        path: str,
        base_params: dict[str, Any],
        items_key: str,
        cap: int,
    ) -> tuple[list[dict], list[dict]]:
        items: list[dict] = []
        pages: list[dict] = []
        cursor = ""
        while True:
            page = self._get(path, {**base_params, "cursor": cursor})
            pages.append(page)
            items.extend(page.get(items_key) or [])
            if not page.get("has_next_page") or len(items) >= cap:
                break
            cursor = page.get("next_cursor") or ""
            if not cursor:
                break
        return items[:cap], pages

    # ---- port methods ----

    def fetch_profile(self, handle: str) -> dict:
        def fetch() -> tuple[dict, dict]:
            raw = self._get("/twitter/user/info", {"userName": handle})
            return raw.get("data") or {}, raw

        return self._cached("user_info", {"userName": handle}, fetch)

    def fetch_last_tweets(self, handle: str, max_count: int) -> list[dict]:
        def fetch() -> tuple[list[dict], list[dict]]:
            return self._paginate(
                "/twitter/user/last_tweets",
                # includeReplies defaults to false on the API — must pass true
                # or signal 3 (replies) is silently dropped.
                {"userName": handle, "includeReplies": "true"},
                items_key="tweets",
                cap=max_count,
            )

        return self._cached(
            "last_tweets",
            {"userName": handle, "max": max_count, "includeReplies": True},
            fetch,
        )

    def fetch_followings(self, handle: str, max_count: int) -> list[dict]:
        def fetch() -> tuple[list[dict], list[dict]]:
            return self._paginate(
                "/twitter/user/followings",
                {"userName": handle, "pageSize": min(200, max_count)},
                items_key="followings",
                cap=max_count,
            )

        return self._cached(
            "followings", {"userName": handle, "max": max_count}, fetch
        )

    def fetch_mentions(self, handle: str, max_count: int) -> list[dict]:
        def fetch() -> tuple[list[dict], list[dict]]:
            return self._paginate(
                "/twitter/user/mentions",
                {"userName": handle},
                items_key="tweets",
                cap=max_count,
            )

        return self._cached(
            "mentions", {"userName": handle, "max": max_count}, fetch
        )
