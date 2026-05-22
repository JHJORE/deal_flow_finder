from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from pydantic import BaseModel

from pipeline.adapters.web.firecrawl_adapter import FirecrawlWebFetcher
from pipeline.entities.errors import FetchError


class _Schema(BaseModel):
    foo: str


@dataclass
class _Doc:
    json: Any
    metadata: dict[str, Any]


@dataclass
class _ScrapeResult:
    data: Any


class FakeV2Client:
    def __init__(
        self,
        *,
        scrape_result: Any = None,
        batch_result: Any = None,
        raises: Exception | None = None,
    ) -> None:
        self._scrape_result = scrape_result
        self._batch_result = batch_result
        self._raises = raises
        self.scrape_calls: list[tuple[str, dict[str, Any]]] = []
        self.batch_calls: list[tuple[list[str], dict[str, Any]]] = []

    def scrape(self, url: str, **kwargs: Any) -> Any:
        if self._raises is not None:
            raise self._raises
        self.scrape_calls.append((url, kwargs))
        return self._scrape_result

    def batch_scrape(self, urls: list[str], **kwargs: Any) -> Any:
        if self._raises is not None:
            raise self._raises
        self.batch_calls.append((urls, kwargs))
        return self._batch_result


def test_fetch_structured_returns_data_json() -> None:
    result = _ScrapeResult(data=_Doc(json={"foo": "bar"}, metadata={}))
    adapter = FirecrawlWebFetcher(FakeV2Client(scrape_result=result))
    assert adapter.fetch_structured("https://example.com", _Schema, "prompt") == {"foo": "bar"}


def test_fetch_structured_raises_when_json_missing() -> None:
    result = _ScrapeResult(data=_Doc(json=None, metadata={}))
    adapter = FirecrawlWebFetcher(FakeV2Client(scrape_result=result))
    with pytest.raises(FetchError):
        adapter.fetch_structured("https://example.com", _Schema, "prompt")


def test_fetch_structured_passes_json_format_and_options() -> None:
    result = _ScrapeResult(data=_Doc(json={"foo": "bar"}, metadata={}))
    fake = FakeV2Client(scrape_result=result)
    FirecrawlWebFetcher(fake).fetch_structured("https://example.com", _Schema, "extract foo")
    _, kwargs = fake.scrape_calls[0]
    assert kwargs["only_main_content"] is True
    assert kwargs["timeout"] == 120_000
    formats = kwargs["formats"]
    assert formats[0]["type"] == "json"
    assert formats[0]["prompt"] == "extract foo"
    assert formats[0]["schema"]["properties"]["foo"]["type"] == "string"


def test_fetch_structured_batch_preserves_input_order() -> None:
    docs = [
        _Doc(json={"foo": "B"}, metadata={"sourceURL": "https://example.com/b"}),
        _Doc(json={"foo": "A"}, metadata={"sourceURL": "https://example.com/a"}),
    ]
    result = _ScrapeResult(data=docs)
    adapter = FirecrawlWebFetcher(FakeV2Client(batch_result=result))
    out = adapter.fetch_structured_batch(
        ["https://example.com/a", "https://example.com/b"], _Schema, "prompt"
    )
    assert [d["foo"] for d in out] == ["A", "B"]


def test_fetch_structured_batch_raises_on_missing_url() -> None:
    docs = [_Doc(json={"foo": "A"}, metadata={"sourceURL": "https://example.com/a"})]
    result = _ScrapeResult(data=docs)
    adapter = FirecrawlWebFetcher(FakeV2Client(batch_result=result))
    with pytest.raises(FetchError):
        adapter.fetch_structured_batch(
            ["https://example.com/a", "https://example.com/b"], _Schema, "prompt"
        )


def test_fetch_structured_batch_empty_short_circuits() -> None:
    fake = FakeV2Client()
    adapter = FirecrawlWebFetcher(fake)
    assert adapter.fetch_structured_batch([], _Schema, "prompt") == []
    assert fake.batch_calls == []


def test_sdk_exception_becomes_fetch_error() -> None:
    adapter = FirecrawlWebFetcher(FakeV2Client(raises=RuntimeError("boom")))
    with pytest.raises(FetchError):
        adapter.fetch_structured("https://example.com", _Schema, "prompt")
