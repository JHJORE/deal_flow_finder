from pathlib import Path
from typing import Any

from firecrawl import Firecrawl

from deal_flow.application.ports.services.web_extractor import WebExtractor
from deal_flow.infrastructure.cache.file_cache import FileCache
from deal_flow.infrastructure.external.firecrawl.schemas import (
    BLOG_POSTS_PROMPT,
    PARTNER_DETAIL_PROMPT,
    PARTNER_LISTING_PROMPT,
    PORTFOLIO_DETAIL_PROMPT,
    PORTFOLIO_LISTING_PROMPT,
    BlogPostPage,
    PartnerDetail,
    PartnerListingPage,
    PortfolioDetail,
    PortfolioListingPage,
)


def _to_dict(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, dict):
        return obj
    return vars(obj)


def _json_payload(doc: Any) -> dict[str, Any]:
    """Pull the structured JSON payload out of a Firecrawl Document."""
    d = _to_dict(doc)
    payload = d.get("json") or (d.get("data") or {}).get("json") or {}
    return _to_dict(payload) if not isinstance(payload, dict) else payload


class FirecrawlExtractor(WebExtractor):
    """The single Firecrawl adapter. Wraps the SDK, owns the on-disk response
    cache, and exposes only the purpose-shaped scrape methods.
    """

    def __init__(self, api_key: str, cache_dir: Path, refresh: bool = False) -> None:
        self._app = Firecrawl(api_key=api_key)
        self._cache = FileCache(cache_dir)
        self._refresh = refresh

    def _cached(self, op: str, key_inputs: dict[str, Any], fetch):
        key = FileCache.key_for(op, **key_inputs)
        if not self._refresh:
            hit = self._cache.read(key)
            if hit is not None:
                return hit["payload"]
        payload, raw = fetch()
        self._cache.write(key, {"op": op, "inputs": key_inputs, "raw": raw, "payload": payload})
        return payload

    def _scrape(self, url: str, schema_cls, prompt: str) -> dict:
        json_format = {
            "type": "json",
            "schema": schema_cls.model_json_schema(),
            "prompt": prompt,
        }

        def fetch():
            doc = self._app.scrape(url, formats=[json_format])
            return _json_payload(doc), _to_dict(doc)

        return self._cached(
            "scrape",
            {"url": url, "schema": schema_cls.__name__, "prompt": prompt},
            fetch,
        )

    def _batch(self, urls: list[str], schema_cls, prompt: str) -> list[dict]:
        json_format = {
            "type": "json",
            "schema": schema_cls.model_json_schema(),
            "prompt": prompt,
        }

        def fetch():
            result = self._app.batch_scrape(urls, formats=[json_format])
            raw = _to_dict(result)
            payloads = [_json_payload(d) for d in (raw.get("data") or [])]
            return payloads, raw

        return self._cached(
            "batch_scrape",
            {"urls": sorted(urls), "schema": schema_cls.__name__, "prompt": prompt},
            fetch,
        )

    def scrape_partner_listing(self, team_url: str) -> list[dict]:
        payload = self._scrape(team_url, PartnerListingPage, PARTNER_LISTING_PROMPT)
        return payload.get("partners") or []

    def scrape_partner_details(self, profile_urls: list[str]) -> list[dict]:
        return self._batch(profile_urls, PartnerDetail, PARTNER_DETAIL_PROMPT)

    def scrape_portfolio_listing(self, portfolio_url: str) -> list[dict]:
        payload = self._scrape(portfolio_url, PortfolioListingPage, PORTFOLIO_LISTING_PROMPT)
        return payload.get("companies") or []

    def scrape_portfolio_details(self, detail_urls: list[str]) -> list[dict]:
        return self._batch(detail_urls, PortfolioDetail, PORTFOLIO_DETAIL_PROMPT)

    def scrape_blog_posts(self, blog_url: str) -> list[dict]:
        payload = self._scrape(blog_url, BlogPostPage, BLOG_POSTS_PROMPT)
        return payload.get("posts") or []
