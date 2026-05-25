from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from deal_flow.application.dtos.team_url import TeamUrl

_REGISTRY_PATH = Path(__file__).resolve().parents[4] / "firms.yaml"


@dataclass(frozen=True)
class FirmSources:
    # Investment-team listing — choose ONE of these two strategies per firm:
    #   (a) team_urls: one or more pages we scrape via Firecrawl LLM extraction.
    #       Each TeamUrl carries optional ``focus_areas`` tags (e.g. Sequoia's
    #       Seed/Early or Growth) that get propagated onto every partner
    #       discovered on that URL — a partner appearing in multiple URLs
    #       ends up with the union of their tags.
    #   (b) team_payload_url + team_payload_attribute + team_payload_role_filter:
    #       the page embeds the entire roster as JSON in a data-* attribute
    #       (e.g. a16z). Cheaper, no LLM. Focus areas come from the JSON.
    team_urls: tuple[TeamUrl, ...] = ()
    team_payload_url: str | None = None
    team_payload_attribute: str | None = None
    team_payload_role_filter: str | None = None

    portfolio_url: str | None = None
    portfolio_sitemap_url: str | None = None
    portfolio_html_json_url: str | None = None
    portfolio_html_json_attribute: str | None = None
    blog_url: str | None = None

    @property
    def team_url(self) -> str | None:
        """First team URL (or payload URL) — convenience for callers that
        only need one URL to identify the team page."""
        if self.team_urls:
            return self.team_urls[0].url
        return self.team_payload_url


def _coerce_team_url(entry: Any) -> TeamUrl:
    """team_urls items can be either a bare URL string or a mapping with
    ``url`` and optional ``focus_areas``. Normalise either shape into a
    ``TeamUrl``."""
    if isinstance(entry, str):
        return TeamUrl(url=entry)
    if isinstance(entry, dict):
        return TeamUrl(
            url=entry["url"],
            focus_areas=tuple(entry.get("focus_areas") or ()),
        )
    raise ValueError(f"team_urls entry must be str or dict, got {type(entry).__name__}")


def _normalise(entry: dict[str, Any]) -> dict[str, Any]:
    """Back-compat for single ``team_url:`` and coerce team_urls entries."""
    entry = {**entry}
    if "team_url" in entry and "team_urls" not in entry:
        url = entry.pop("team_url")
        if url:
            entry["team_urls"] = [url]
    if entry.get("team_urls"):
        entry["team_urls"] = tuple(_coerce_team_url(e) for e in entry["team_urls"])
    else:
        entry.pop("team_urls", None)
    return entry


def load_registry(path: Path = _REGISTRY_PATH) -> dict[str, FirmSources]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {domain: FirmSources(**_normalise(entry)) for domain, entry in raw.items()}
