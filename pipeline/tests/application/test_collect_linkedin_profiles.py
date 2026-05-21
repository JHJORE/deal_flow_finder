from __future__ import annotations

from pipeline.application.use_cases.collect_linkedin_profiles import CollectLinkedInProfiles
from pipeline.entities.models import LinkedInProfile
from pipeline.entities.value_objects import Timestamp, Url
from pipeline.tests.application.fakes import FakeLinkedInFetcher, FakeRepository


def _profile(title: str = "Founder") -> LinkedInProfile:
    return LinkedInProfile(
        linkedin_url=Url("https://linkedin.com/in/alice"),
        captured_at=Timestamp.now(),
        current_title=title,
        current_company="Stealth",
        headline="building",
        recent_role_change=False,
    )


def test_persists_profile_and_no_transition_on_first_capture() -> None:
    fetcher = FakeLinkedInFetcher(profiles={"https://linkedin.com/in/alice": _profile("PM")})
    repo = FakeRepository()
    out = CollectLinkedInProfiles(linkedin=fetcher, repo=repo).execute(
        [Url("https://linkedin.com/in/alice")]
    )
    assert out[0].transitioned is False
    assert repo.store["linkedin/alice"]["current_title"] == "PM"


def test_detects_title_transition() -> None:
    repo = FakeRepository()
    repo.store["linkedin/alice"] = {"current_title": "PM at Ramp"}
    fetcher = FakeLinkedInFetcher(profiles={"https://linkedin.com/in/alice": _profile("Stealth")})
    out = CollectLinkedInProfiles(linkedin=fetcher, repo=repo).execute(
        [Url("https://linkedin.com/in/alice")]
    )
    assert out[0].transitioned is True
    assert out[0].prior_title == "PM at Ramp"


def test_missing_profile_is_skipped() -> None:
    fetcher = FakeLinkedInFetcher(profiles={})
    repo = FakeRepository()
    out = CollectLinkedInProfiles(linkedin=fetcher, repo=repo).execute(
        [Url("https://linkedin.com/in/ghost")]
    )
    assert out == []
