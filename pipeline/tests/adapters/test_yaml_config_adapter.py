from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.adapters.config.yaml_config_adapter import YamlConfigRepository
from pipeline.entities.errors import ValidationError
from pipeline.entities.value_objects import FirmName


def _write(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def _repo(tmp_path: Path) -> YamlConfigRepository:
    return YamlConfigRepository(
        firms_path=tmp_path / "firms.yaml",
        watchlist_path=tmp_path / "watchlist.yaml",
        handle_overrides_path=tmp_path / "overrides.yaml",
    )


def test_load_firms(tmp_path: Path) -> None:
    _write(
        tmp_path / "firms.yaml",
        """
firms:
  sequoia:
    team: https://sequoiacap.com/people
    portfolio: https://sequoiacap.com/companies
    blog: https://sequoiacap.com/perspective
""",
    )
    firms = _repo(tmp_path).load_firms()
    assert len(firms) == 1
    assert firms[0].name is FirmName.SEQUOIA
    assert firms[0].team_url.value == "https://sequoiacap.com/people"


def test_load_watchlist_skips_invalid_entries(tmp_path: Path) -> None:
    _write(
        tmp_path / "watchlist.yaml",
        """
operators:
  - name: Cristina Cordova
    linkedin_url: https://linkedin.com/in/cristinajcordova
    prior_employer: Notion
  - name: Bad Entry
    linkedin_url: not-a-url
    prior_employer: Stripe
""",
    )
    entries = _repo(tmp_path).load_watchlist()
    assert [e.name for e in entries] == ["Cristina Cordova"]


def test_handle_overrides_optional(tmp_path: Path) -> None:
    # File absent — should return empty dict, not raise.
    assert _repo(tmp_path).load_handle_overrides() == {}

    _write(
        tmp_path / "overrides.yaml",
        """
overrides:
  Roelof Botha: roelofbotha
  Empty Value:
""",
    )
    overrides = _repo(tmp_path).load_handle_overrides()
    assert overrides == {"Roelof Botha": "roelofbotha"}


def test_malformed_yaml_becomes_validation_error(tmp_path: Path) -> None:
    _write(tmp_path / "firms.yaml", "firms: [unterminated")
    with pytest.raises(ValidationError):
        _repo(tmp_path).load_firms()
