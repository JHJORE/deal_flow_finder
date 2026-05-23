from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from firecrawl import Firecrawl

from deal_flow.application.ports.services.web_extractor import WebExtractor
from deal_flow.infrastructure.external.firecrawl.cache import FileCache
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

# /map ``search`` keyword + URL-path whitelist for picking the right link.
_SECTION_TARGETS: dict[str, tuple[str, tuple[str, ...]]] = {
    "team": ("team", ("/team", "/people", "/our-team", "/our-people", "/about/people")),
    "portfolio": ("portfolio", ("/portfolio", "/companies", "/investments", "/our-companies")),
    "blog": (
        "blog news insights",
        ("/blog", "/news", "/insights", "/news-content", "/perspectives", "/articles"),
    ),
}


def _normalize(firm_domain: str) -> tuple[str, str]:
    raw = firm_domain.strip().rstrip("/")
    if "://" not in raw:
        raw = f"https://{raw}"
    parsed = urlparse(raw)
    host = (parsed.netloc or parsed.path).lower().removeprefix("www.")
    return f"https://{host}", host


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


def _pick_section_url(links: list[dict], host: str, keywords: tuple[str, ...]) -> str | None:
    for link in links:
        url = link.get("url")
        if not url:
            continue
        parsed = urlparse(url)
        if parsed.netloc.lower().removeprefix("www.") != host:
            continue
        if any(k in parsed.path.lower() for k in keywords):
            return url
    return None


class FirecrawlExtractor(WebExtractor):
    """The single Firecrawl adapter. Wraps the SDK, owns the on-disk response
    cache, and exposes only the purpose-shaped methods the application needs.
    """

    def __init__(self, api_key: str, cache_dir: Path, refresh: bool = False) -> None:
        self._app = Firecrawl(api_key=api_key)
        self._cache = FileCache(cache_dir)
        self._refresh = refresh

    # ---- caching ----

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

    # ---- WebExtractor ----

    def discover_firm_sections(self, firm_domain: str) -> dict[str, str | None]:
        base_url, host = _normalize(firm_domain)

        def fetch_map(search: str):
            def go():
                result = self._app.map(base_url, search=search, limit=20)
                raw = _to_dict(result)
                links = [_to_dict(link) for link in (raw.get("links") or [])]
                return links, raw

            return self._cached("map", {"url": base_url, "search": search}, go)

        sections: dict[str, str | None] = {}
        for key, (search, keywords) in _SECTION_TARGETS.items():
            sections[key] = _pick_section_url(fetch_map(search), host, keywords)
        return sections

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
        return self._scrape(blog_url, BlogPostPage, BLOG_POSTS_PROMPT).get("posts") or []
