"""Firecrawl v2 adapter — structured JSON extraction only.

The pipeline pays Firecrawl to do LLM-driven structured extraction; we never
parse markdown ourselves. This adapter exposes two methods:

* :meth:`fetch_structured` — single-URL JSON scrape against a Pydantic schema.
* :meth:`fetch_structured_batch` — parallel batch scrape of many URLs against
  the same schema, results returned in the input URL order.

Coded against firecrawl-py v2 (``from firecrawl import Firecrawl``). Result
shape is ``result.data.json`` per the v2 docs.
"""

from __future__ import annotations

import sys
from typing import Any, Protocol

from pydantic import BaseModel

from pipeline.entities.errors import FetchError


class _FirecrawlV2Client(Protocol):
    """Subset of the v2 SDK surface we depend on. Lets tests inject a fake."""

    def scrape(self, url: str, **kwargs: Any) -> Any: ...

    def batch_scrape(self, urls: list[str], **kwargs: Any) -> Any: ...


_DEFAULT_TIMEOUT_MS = 120_000


class FirecrawlWebFetcher:
    """Adapter over a Firecrawl v2 ``Firecrawl`` client."""

    def __init__(self, client: _FirecrawlV2Client) -> None:
        self._client = client

    def fetch_structured(
        self, url: str, schema_cls: type[BaseModel], prompt: str
    ) -> dict[str, Any]:
        formats = [_json_format(schema_cls, prompt)]
        _log(f"firecrawl scrape: {url}")
        try:
            result = self._client.scrape(
                url,
                formats=formats,
                only_main_content=True,
                timeout=_DEFAULT_TIMEOUT_MS,
            )
        except Exception as exc:
            raise FetchError(f"firecrawl scrape failed for {url}: {exc}") from exc

        return _extract_json(result, source_url=url)

    def fetch_structured_batch(
        self, urls: list[str], schema_cls: type[BaseModel], prompt: str
    ) -> list[dict[str, Any]]:
        if not urls:
            return []
        formats = [_json_format(schema_cls, prompt)]
        for url in urls:
            _log(f"firecrawl batch_scrape: {url}")
        try:
            result = self._client.batch_scrape(
                urls,
                formats=formats,
                only_main_content=True,
                timeout=_DEFAULT_TIMEOUT_MS,
            )
        except Exception as exc:
            raise FetchError(f"firecrawl batch_scrape failed: {exc}") from exc

        return _extract_batch_json(result, requested_urls=urls)


def _json_format(schema_cls: type[BaseModel], prompt: str) -> dict[str, Any]:
    return {
        "type": "json",
        "schema": schema_cls.model_json_schema(),
        "prompt": prompt,
    }


def _extract_json(result: Any, *, source_url: str) -> dict[str, Any]:
    """Pull ``result.data.json`` out of a v2 scrape response.

    Coded against the v2 docs — no defensive fallback chain. If the SDK shape
    differs, we want a clear failure on first run, not a silent shim.
    """
    data = getattr(result, "data", None)
    if data is None:
        raise FetchError(f"firecrawl returned no .data for {source_url}: {result!r}")
    payload = getattr(data, "json", None)
    if payload is None:
        raise FetchError(f"firecrawl returned no .data.json for {source_url}: {data!r}")
    if not isinstance(payload, dict):
        raise FetchError(
            f"firecrawl .data.json for {source_url} is {type(payload).__name__}, expected dict"
        )
    return payload


def _extract_batch_json(result: Any, *, requested_urls: list[str]) -> list[dict[str, Any]]:
    """Pull per-URL JSON payloads from a v2 batch_scrape response, in input order.

    v2 ``batch_scrape`` returns a job with ``.data`` as a list of documents;
    each doc carries its source URL in ``doc.metadata.source_url`` (or
    ``.url``). We index by URL and reorder against ``requested_urls`` so the
    caller can zip results to inputs.
    """
    docs = getattr(result, "data", None)
    if docs is None:
        raise FetchError(f"firecrawl batch returned no .data: {result!r}")
    if not isinstance(docs, list):
        raise FetchError(f"firecrawl batch .data is {type(docs).__name__}, expected list")

    by_url: dict[str, dict[str, Any]] = {}
    for doc in docs:
        metadata = getattr(doc, "metadata", None)
        url = _doc_url(metadata)
        payload = getattr(doc, "json", None)
        if url is None:
            raise FetchError(f"firecrawl batch doc missing source URL: {doc!r}")
        if payload is None:
            raise FetchError(f"firecrawl batch doc {url!r} missing .json: {doc!r}")
        if not isinstance(payload, dict):
            raise FetchError(
                f"firecrawl batch doc {url!r} .json is {type(payload).__name__}, expected dict"
            )
        by_url[url] = payload

    out: list[dict[str, Any]] = []
    for url in requested_urls:
        if url not in by_url:
            raise FetchError(f"firecrawl batch missing result for requested URL: {url}")
        out.append(by_url[url])
    return out


def _doc_url(metadata: Any) -> str | None:
    """Read the source URL off a v2 Document's metadata.

    Coded against the v2 docs: ``metadata.sourceURL`` (camelCase). Accepts
    metadata as a dict or as an object with attribute access — that's a shape
    variation in the SDK itself, not a value-key fallback.
    """
    if metadata is None:
        return None
    if isinstance(metadata, dict):
        value = metadata.get("sourceURL")
    else:
        value = getattr(metadata, "sourceURL", None)
    return value if isinstance(value, str) and value else None


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)
