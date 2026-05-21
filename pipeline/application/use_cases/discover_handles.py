"""Discover X handles for partners and founders.

Strategy, in order:
1. Honour ``config/handle_overrides.yaml`` — a manual escape hatch.
2. Trust handles already present on the entity (extracted from the firm page).
3. Best-effort: do nothing programmatic here. Live handle discovery is a
   per-person research task; we surface the unresolved list so a human can
   complete the file and re-run.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from pipeline.entities.errors import ValidationError
from pipeline.entities.models import Founder, Partner
from pipeline.entities.value_objects import Handle


@dataclass(frozen=True, slots=True)
class HandleDiscoveryResult:
    partners: tuple[Partner, ...]
    founders: tuple[Founder, ...]
    unresolved_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DiscoverHandles:
    overrides: dict[str, str]

    def execute(self, partners: list[Partner], founders: list[Founder]) -> HandleDiscoveryResult:
        resolved_partners: list[Partner] = []
        resolved_founders: list[Founder] = []
        unresolved: list[str] = []

        for p in partners:
            override = self._override_for(p.name)
            handle = override or p.x_handle
            if handle is None:
                unresolved.append(p.name)
            resolved_partners.append(replace(p, x_handle=handle))

        for f in founders:
            override = self._override_for(f.name)
            handle = override or f.x_handle
            if handle is None:
                unresolved.append(f.name)
            resolved_founders.append(replace(f, x_handle=handle))

        return HandleDiscoveryResult(
            partners=tuple(resolved_partners),
            founders=tuple(resolved_founders),
            unresolved_names=tuple(unresolved),
        )

    def _override_for(self, name: str) -> Handle | None:
        raw = self.overrides.get(name) or self.overrides.get(name.lower())
        if not raw:
            return None
        try:
            return Handle(raw)
        except ValidationError:
            return None
