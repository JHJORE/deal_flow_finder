"""Collect LinkedIn profile data for partners, founders, and operator watchlist.

Title-transition detection: if a prior snapshot exists in the repository
under ``linkedin/<slug>``, compare its ``current_title`` against the new
fetch. The transition flag becomes the data foundation for the Tier 3
``OPERATOR_STEALTH_TRANSITION`` signal — the actual detection lives in the
next workspace.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pipeline.application.ports.linkedin import LinkedInFetcher
from pipeline.application.ports.repository import EntityRepository
from pipeline.entities.errors import DomainError
from pipeline.entities.models import LinkedInProfile
from pipeline.entities.value_objects import Url


@dataclass(frozen=True, slots=True)
class ProfileChange:
    linkedin_url: Url
    profile: LinkedInProfile
    prior_title: str | None
    transitioned: bool


@dataclass(frozen=True, slots=True)
class CollectLinkedInProfiles:
    linkedin: LinkedInFetcher
    repo: EntityRepository

    def execute(self, linkedin_urls: list[Url]) -> list[ProfileChange]:
        out: list[ProfileChange] = []
        for url in linkedin_urls:
            try:
                profile = self.linkedin.fetch_profile(url)
            except DomainError:
                continue
            if profile is None:
                continue

            slug = _slug(url)
            prior = self.repo.load(f"linkedin/{slug}")
            prior_title = (prior or {}).get("current_title") if isinstance(prior, dict) else None
            transitioned = bool(prior_title) and prior_title != profile.current_title

            self.repo.save(f"linkedin/{slug}", _serialise(profile, prior_title))
            out.append(
                ProfileChange(
                    linkedin_url=url,
                    profile=profile,
                    prior_title=prior_title,
                    transitioned=transitioned,
                )
            )
        return out


def _slug(url: Url) -> str:
    # LinkedIn profile URLs look like https://linkedin.com/in/<slug>/
    return url.value.rstrip("/").rsplit("/", 1)[-1]


def _serialise(profile: LinkedInProfile, prior_title: str | None) -> dict[str, Any]:
    return {
        "linkedin_url": profile.linkedin_url.value,
        "captured_at": profile.captured_at.iso(),
        "current_title": profile.current_title,
        "current_company": profile.current_company,
        "headline": profile.headline,
        "recent_role_change": profile.recent_role_change,
        "prior_title": prior_title,
    }
