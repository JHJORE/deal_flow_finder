from __future__ import annotations

from pathlib import Path

import httpx
import respx

from pipeline.adapters.linkedin.proxycurl_adapter import (
    COMPANY_ENDPOINT,
    PROFILE_ENDPOINT,
    ProxycurlLinkedInFetcher,
)
from pipeline.entities.value_objects import Url


def _fetcher(tmp_path: Path) -> ProxycurlLinkedInFetcher:
    return ProxycurlLinkedInFetcher(httpx.Client(), tmp_path / "cache")


@respx.mock
def test_profile_fetch_and_cache(tmp_path: Path) -> None:
    url = Url("https://linkedin.com/in/alice")
    route = respx.get(PROFILE_ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            json={
                "headline": "Building",
                "experiences": [{"title": "Founder", "company": "Stealth"}],
            },
        )
    )

    fetcher = _fetcher(tmp_path)
    profile = fetcher.fetch_profile(url)
    assert profile is not None
    assert profile.current_title == "Founder"

    # Second call must hit the cache, not the network.
    profile2 = fetcher.fetch_profile(url)
    assert profile2 is not None
    assert route.call_count == 1


@respx.mock
def test_profile_404_returns_none(tmp_path: Path) -> None:
    respx.get(PROFILE_ENDPOINT).mock(return_value=httpx.Response(404))
    assert _fetcher(tmp_path).fetch_profile(Url("https://linkedin.com/in/ghost")) is None


@respx.mock
def test_company_fetch(tmp_path: Path) -> None:
    respx.get(COMPANY_ENDPOINT).mock(
        return_value=httpx.Response(200, json={"name": "Stripe", "company_size_on_linkedin": 7000})
    )
    company = _fetcher(tmp_path).fetch_company(Url("https://linkedin.com/company/stripe"))
    assert company is not None
    assert company.name == "Stripe"
    assert company.headcount == 7000
