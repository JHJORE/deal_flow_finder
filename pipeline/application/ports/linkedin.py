"""LinkedIn data port."""

from __future__ import annotations

from typing import Protocol

from pipeline.entities.models import LinkedInCompany, LinkedInProfile
from pipeline.entities.value_objects import Url


class LinkedInFetcher(Protocol):
    def fetch_profile(self, linkedin_url: Url) -> LinkedInProfile | None: ...

    def fetch_company(self, linkedin_url: Url) -> LinkedInCompany | None: ...
