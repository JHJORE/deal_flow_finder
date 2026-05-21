"""YAML implementation of ``ConfigRepository``.

The only file in the codebase that imports ``yaml``. Translates YAML
documents into domain entities; any malformed entry raises
:class:`DomainError` (specifically ``ValidationError``) rather than letting
a ``yaml.YAMLError`` leak through.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from pipeline.entities.errors import ValidationError
from pipeline.entities.models import Firm, WatchlistEntry
from pipeline.entities.value_objects import FirmName, Url


class YamlConfigRepository:
    """Read firms / watchlist / handle overrides from ``config/*.yaml``."""

    def __init__(
        self,
        firms_path: Path,
        watchlist_path: Path,
        handle_overrides_path: Path,
    ) -> None:
        self._firms_path = firms_path
        self._watchlist_path = watchlist_path
        self._handle_overrides_path = handle_overrides_path

    def load_firms(self) -> list[Firm]:
        raw = _load_yaml(self._firms_path)
        firms_raw = raw.get("firms")
        if not isinstance(firms_raw, list):
            raise ValidationError(f"{self._firms_path}: expected a 'firms' list")
        firms: list[Firm] = []
        for entry in firms_raw:
            if not isinstance(entry, dict):
                raise ValidationError(
                    f"{self._firms_path}: firm entry must be a mapping, "
                    f"got {type(entry).__name__}"
                )
            firms.append(
                Firm(
                    name=FirmName(entry["name"]),
                    website=Url(entry["website"]),
                    people_page_url=Url(entry["people_page_url"]),
                    portfolio_page_url=Url(entry["portfolio_page_url"]),
                    blog_url=Url(entry["blog_url"]) if entry.get("blog_url") else None,
                )
            )
        return firms

    def load_watchlist(self) -> list[WatchlistEntry]:
        if not self._watchlist_path.exists():
            return []
        raw = _load_yaml(self._watchlist_path)
        entries_raw = raw.get("operators")
        if not isinstance(entries_raw, list):
            raise ValidationError(f"{self._watchlist_path}: expected an 'operators' list")
        out: list[WatchlistEntry] = []
        for entry in entries_raw:
            if not isinstance(entry, dict):
                continue
            try:
                out.append(
                    WatchlistEntry(
                        name=str(entry["name"]),
                        linkedin_url=Url(entry["linkedin_url"]),
                        prior_employer=str(entry.get("prior_employer", "")),
                    )
                )
            except (KeyError, ValidationError):
                continue
        return out

    def load_handle_overrides(self) -> dict[str, str]:
        if not self._handle_overrides_path.exists():
            return {}
        raw = _load_yaml(self._handle_overrides_path)
        overrides = raw.get("overrides") or {}
        if not isinstance(overrides, dict):
            return {}
        return {str(k): str(v) for k, v in overrides.items() if v}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:
        raise ValidationError(f"{path}: malformed YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError(f"{path}: expected top-level mapping, got {type(data).__name__}")
    return data
