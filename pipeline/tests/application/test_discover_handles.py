from __future__ import annotations

from pipeline.application.use_cases.discover_handles import DiscoverHandles
from pipeline.entities.models import Founder, Partner, new_id
from pipeline.entities.value_objects import FirmName, Handle


def _partner(name: str, handle: Handle | None = None) -> Partner:
    return Partner(
        id=new_id(),
        name=name,
        firm=FirmName.SEQUOIA,
        role="Partner",
        x_handle=handle,
        linkedin_url=None,
        blog_url=None,
        bio="",
    )


def test_applies_override_when_handle_missing() -> None:
    uc = DiscoverHandles(overrides={"Roelof Botha": "roelofbotha"})
    result = uc.execute([_partner("Roelof Botha")], [])
    assert result.partners[0].x_handle == Handle("roelofbotha")
    assert result.unresolved_names == ()


def test_keeps_existing_handle_when_no_override() -> None:
    uc = DiscoverHandles(overrides={})
    result = uc.execute([_partner("Alfred Lin", Handle("Alfred_Lin"))], [])
    assert result.partners[0].x_handle == Handle("Alfred_Lin")


def test_reports_unresolved() -> None:
    uc = DiscoverHandles(overrides={})
    result = uc.execute([_partner("Mystery Person")], [])
    assert result.unresolved_names == ("Mystery Person",)


def test_founders_also_resolved() -> None:
    founder = Founder(
        id=new_id(),
        name="Patrick Collison",
        x_handle=None,
        linkedin_url=None,
        company_id=None,
        role="CEO",
        prior_employer=None,
    )
    uc = DiscoverHandles(overrides={"Patrick Collison": "patrickc"})
    result = uc.execute([], [founder])
    assert result.founders[0].x_handle == Handle("patrickc")
