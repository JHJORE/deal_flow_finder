import html as html_lib
import json as _json
import re
import urllib.request
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


def _source_url(doc: Any) -> str | None:
    """The URL that was actually scraped to produce this Document. Firecrawl
    batches return items in completion order, not request order, so this is
    the only safe join key back to the input URL list.
    """
    d = _to_dict(doc)
    md = _to_dict(d.get("metadata") or {})
    return md.get("url") or md.get("source_url") or md.get("sourceURL") or md.get("og:url")


def _og_image(doc: Any) -> str | None:
    """Portrait URL straight from the page's Open Graph metadata. Reliable for
    partner / company profile pages where og:image is the social-share image.
    """
    md = _to_dict(_to_dict(doc).get("metadata") or {})
    return md.get("og_image") or md.get("og:image") or md.get("ogImage")


def _has_substantive_content(doc: Any, min_chars: int = 200) -> bool:
    """True if Firecrawl actually got page content. Three acceptance paths:
    (1) raw markdown/html length above the threshold,
    (2) extracted `json` has at least 2 populated scalar-ish fields, or
    (3) extracted `json` contains any list field with at least 3 items.

    Firecrawl strips raw markdown when only json format is requested even on
    successful scrapes, so paths (2) and (3) catch json-only responses with
    substantive structure. Listing-style responses (one `items: [...]` field)
    are handled by path 3; detail-style responses (several scalars) by path 2.

    Guards against the inverse: a JS-rendered page that came back empty,
    where the LLM might still fabricate structured output from nothing.
    """
    d = _to_dict(doc)
    if sum(len(d.get(k) or "") for k in ("markdown", "html", "raw_html")) >= min_chars:
        return True
    j = d.get("json") or {}
    if isinstance(j, dict):
        populated = sum(1 for v in j.values() if v not in (None, "", [], {}, ()))
        if populated >= 2:
            return True
        for v in j.values():
            if isinstance(v, list) and len(v) >= 3:
                return True
    return False


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
        payload, _raw = fetch()
        self._cache.write(key, {"op": op, "inputs": key_inputs, "payload": payload})
        return payload

    def _scrape(
        self,
        url: str,
        schema_cls,
        prompt: str,
        *,
        wait_for: int | None = None,
        actions: list[dict] | None = None,
        proxy: str | None = None,
    ) -> dict:
        json_format = {
            "type": "json",
            "schema": schema_cls.model_json_schema(),
            "prompt": prompt,
        }
        if wait_for is not None and not actions:
            actions = [{"type": "wait", "milliseconds": wait_for}]
        sdk_kwargs: dict[str, Any] = {"formats": ["markdown", json_format]}
        if actions:
            sdk_kwargs["actions"] = actions
        if proxy:
            sdk_kwargs["proxy"] = proxy

        def fetch():
            doc = self._app.scrape(url, **sdk_kwargs)
            if not _has_substantive_content(doc):
                print(
                    f"[firecrawl] WARN: empty content for {url} — refusing to trust LLM "
                    "output (likely JS-rendered page; raise wait_for or add actions)."
                )
                return {}, _to_dict(doc)
            return _json_payload(doc), _to_dict(doc)

        return self._cached(
            "scrape",
            {
                "url": url,
                "schema": schema_cls.__name__,
                "prompt": prompt,
                "wait_for": wait_for,
                "actions": actions,
                "proxy": proxy,
            },
            fetch,
        )

    def _batch(
        self,
        urls: list[str],
        schema_cls,
        prompt: str,
        *,
        wait_for: int | None = None,
        actions: list[dict] | None = None,
        proxy: str | None = None,
    ) -> dict[str, dict]:
        json_format = {
            "type": "json",
            "schema": schema_cls.model_json_schema(),
            "prompt": prompt,
        }
        if wait_for is not None and not actions:
            actions = [{"type": "wait", "milliseconds": wait_for}]
        sdk_kwargs: dict[str, Any] = {"formats": ["markdown", json_format]}
        if actions:
            sdk_kwargs["actions"] = actions
        if proxy:
            sdk_kwargs["proxy"] = proxy

        def fetch():
            result = self._app.batch_scrape(urls, **sdk_kwargs)
            raw = _to_dict(result)
            payload: dict[str, dict] = {}
            for doc in raw.get("data") or []:
                if not _has_substantive_content(doc):
                    print(
                        f"[firecrawl] WARN: empty content for {_source_url(doc)} — skipped."
                    )
                    continue
                src = _source_url(doc)
                if src:
                    j = _json_payload(doc)
                    j["photo_url"] = _og_image(doc)
                    payload[src] = j
            return payload, raw

        return self._cached(
            "batch_scrape",
            {
                "urls": sorted(urls),
                "schema": schema_cls.__name__,
                "prompt": prompt,
                "wait_for": wait_for,
                "actions": actions,
                "proxy": proxy,
            },
            fetch,
        )

    def scrape_partner_listing(self, team_url: str) -> list[dict]:
        payload = self._scrape(team_url, PartnerListingPage, PARTNER_LISTING_PROMPT)
        return payload.get("partners") or []

    def scrape_partner_details(self, profile_urls: list[str]) -> dict[str, dict]:
        return self._batch(profile_urls, PartnerDetail, PARTNER_DETAIL_PROMPT)

    def scrape_portfolio_listing(self, portfolio_url: str) -> list[dict]:
        payload = self._scrape(
            portfolio_url,
            PortfolioListingPage,
            PORTFOLIO_LISTING_PROMPT,
            proxy="auto",
        )
        return payload.get("companies") or []

    def discover_portfolio_from_html_json(
        self, listing_url: str, attribute_name: str, limit: int
    ) -> list[dict]:
        req = urllib.request.Request(listing_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        m = re.search(rf'{re.escape(attribute_name)}="([^"]+)"', raw)
        if not m:
            return []
        entries = _json.loads(html_lib.unescape(m.group(1)))
        out: list[dict] = []
        for e in entries[:limit]:
            linkedin = next(
                (s.get("url") for s in (e.get("socials") or [])
                 if isinstance(s, dict) and "linkedin" in _json.dumps(s).lower()),
                None,
            )
            founders_csv = (e.get("founders_list") or "").strip()
            founders = [
                {"name": n.strip(), "role": None}
                for n in founders_csv.split(",")
                if n.strip()
            ]
            out.append({
                "name": e.get("name") or e.get("post_title") or "",
                "detail_url": e.get("permalink") or "",
                "website": e.get("url") or e.get("external_url") or e.get("company_url"),
                "sector": e.get("verticals") or None,
                "description": e.get("website_description") or None,
                "linkedin_url": linkedin,
                "photo_url": e.get("logo") or None,
                "founders": founders,
            })
        return out

    def discover_portfolio_urls_from_sitemap(
        self, sitemap_url: str, limit: int
    ) -> list[dict]:
        req = urllib.request.Request(sitemap_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml = resp.read().decode("utf-8", errors="replace")
        urls = re.findall(r"<loc>([^<]+)</loc>", xml)
        urls.sort(key=lambda u: u.rstrip("/").rsplit("/", 1)[-1].lower())
        out: list[dict] = []
        for u in urls[:limit]:
            slug = u.rstrip("/").rsplit("/", 1)[-1]
            out.append({"name": slug.replace("-", " ").title(), "detail_url": u})
        return out

    def scrape_portfolio_details(self, detail_urls: list[str]) -> dict[str, dict]:
        return self._batch(
            detail_urls,
            PortfolioDetail,
            PORTFOLIO_DETAIL_PROMPT,
            proxy="auto",
        )

    def scrape_blog_posts(self, blog_url: str) -> list[dict]:
        payload = self._scrape(
            blog_url,
            BlogPostPage,
            BLOG_POSTS_PROMPT,
            wait_for=5000,
        )
        return payload.get("posts") or []

    def search_x_profile(self, firm_name: str, partner_name: str) -> str | None:
        """Find a partner's X profile URL via Firecrawl's web search.

        Used as a fallback when the firm's team page didn't surface an X link.
        Returns canonical ``https://x.com/<handle>`` or ``None``.
        """
        def fetch() -> tuple[str | None, Any]:
            result = self._app.search(
                query=f'"{partner_name}" {firm_name} (site:x.com OR site:twitter.com)',
                limit=10,
                include_domains=["x.com", "twitter.com"],
            )
            raw = _to_dict(result)
            for item in raw.get("web") or []:
                normalized = _validate_x_profile_url(_to_dict(item).get("url") or "")
                if normalized:
                    return normalized, raw
            return None, raw

        return self._cached(
            "search_x_profile",
            {"firm_name": firm_name, "partner_name": partner_name},
            fetch,
        )


_TWITTER_HOSTS = {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}
_HANDLE_RE = re.compile(r"^[A-Za-z0-9_]{1,15}$")
_RESERVED_X_PATHS = {
    "home", "explore", "notifications", "messages", "search", "i", "intent",
    "share", "compose", "settings", "login", "signup", "tos", "privacy",
    "about", "status",
}


def _validate_x_profile_url(url: str) -> str | None:
    """Canonicalize ``url`` to ``https://x.com/<handle>`` if it's a real X
    profile, else ``None``. Filters search/intent/status pages and reserved
    usernames."""
    if not url:
        return None
    from urllib.parse import urlparse
    parsed = urlparse(url.strip())
    if (parsed.netloc or "").lower() not in _TWITTER_HOSTS:
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if not parts or not _HANDLE_RE.match(parts[0]) or parts[0].lower() in _RESERVED_X_PATHS:
        return None
    return f"https://x.com/{parts[0]}"
