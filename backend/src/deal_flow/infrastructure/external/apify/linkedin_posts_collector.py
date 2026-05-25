from collections.abc import Sequence
from pathlib import Path
from typing import Any

import httpx

from deal_flow.application.ports.services.linkedin_collector import LinkedInCollector
from deal_flow.infrastructure.cache.file_cache import FileCache


class ApifyRunError(RuntimeError):
    """Raised when an Apify actor run returns a non-2xx response."""


class HarvestApiLinkedInCollector(LinkedInCollector):
    """``LinkedInCollector`` backed by Apify's ``harvestapi/linkedin-profile-posts``.

    Per-URL cache: a batch call with N URLs only sends the cache misses to
    Apify and writes one cache entry per URL afterwards, so subsequent calls
    that overlap don't re-spend credits.
    """

    BASE_URL = "https://api.apify.com"
    _OP = "apify_linkedin_posts"

    def __init__(
        self,
        api_token: str,
        actor_id: str,
        cache_dir: Path,
        refresh: bool = False,
    ) -> None:
        if not api_token:
            raise ValueError("APIFY_API_TOKEN is not set")
        self._actor_id = actor_id
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {api_token}"},
            # Apify's run-sync caps at 300s; give a little headroom to receive
            # the proper timeout error rather than tearing the connection.
            timeout=httpx.Timeout(360.0),
        )
        self._cache = FileCache(cache_dir)
        self._refresh = refresh

    def fetch_posts(
        self,
        profile_urls: Sequence[str],
        *,
        max_posts: int,
        include_reactions: bool = False,
        include_comments: bool = False,
        max_reactions: int = 5,
        max_comments: int = 5,
        posted_limit: str | None = None,
    ) -> dict[str, list[dict]]:
        options = {
            "max_posts": max_posts,
            "include_reactions": include_reactions,
            "include_comments": include_comments,
            "max_reactions": max_reactions,
            "max_comments": max_comments,
            "posted_limit": posted_limit,
        }

        results: dict[str, list[dict]] = {}
        misses: list[str] = []
        for url in profile_urls:
            cached = self._read_cache(url, options)
            if cached is not None:
                results[url] = cached
            else:
                misses.append(url)

        if misses:
            grouped = self._run_actor(misses, options)
            for url in misses:
                items = grouped.get(url, [])
                results[url] = items
                self._write_cache(url, options, items)
        return results

    def _cache_key(self, url: str, options: dict[str, Any]) -> str:
        return FileCache.key_for(self._OP, url=url, **options)

    def _read_cache(self, url: str, options: dict[str, Any]) -> list[dict] | None:
        if self._refresh:
            return None
        hit = self._cache.read(self._cache_key(url, options))
        return hit["payload"] if hit else None

    def _write_cache(
        self, url: str, options: dict[str, Any], items: list[dict]
    ) -> None:
        self._cache.write(
            self._cache_key(url, options),
            {"op": self._OP, "url": url, "options": options, "payload": items},
        )

    def _run_actor(
        self, urls: list[str], options: dict[str, Any]
    ) -> dict[str, list[dict]]:
        body: dict[str, Any] = {
            "targetUrls": urls,
            "maxPosts": options["max_posts"],
            "scrapeReactions": options["include_reactions"],
            "scrapeComments": options["include_comments"],
            "maxReactions": options["max_reactions"],
            "maxComments": options["max_comments"],
        }
        if options["posted_limit"]:
            body["postedLimit"] = options["posted_limit"]

        resp = self._client.post(
            f"/v2/acts/{self._actor_id}/run-sync-get-dataset-items", json=body
        )
        if resp.status_code >= 400:
            raise ApifyRunError(f"{resp.status_code}: {resp.text[:1000]}")

        grouped: dict[str, list[dict]] = {u: [] for u in urls}
        for row in resp.json():
            source = row.get("inputUrl")
            if source in grouped:
                grouped[source].append(row)
        return grouped
