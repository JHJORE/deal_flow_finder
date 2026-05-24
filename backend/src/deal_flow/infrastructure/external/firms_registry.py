from dataclasses import dataclass
from pathlib import Path

import yaml

_REGISTRY_PATH = Path(__file__).resolve().parents[4] / "firms.yaml"


@dataclass(frozen=True)
class FirmSources:
    team_url: str | None = None
    portfolio_url: str | None = None
    blog_url: str | None = None


def load_registry(path: Path = _REGISTRY_PATH) -> dict[str, FirmSources]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {domain: FirmSources(**entry) for domain, entry in raw.items()}
