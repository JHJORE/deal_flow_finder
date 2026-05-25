"""Shared fakes for unit tests across use cases and routes."""

from collections.abc import Sequence

from deal_flow.application.ports.repositories.partner_directory import (
    PartnerDirectory,
)
from deal_flow.application.ports.services.linkedin_collector import LinkedInCollector
from deal_flow.domain.entities.partner import Partner


class FakePartnerDirectory(PartnerDirectory):
    def __init__(self, partners: list[Partner]) -> None:
        self.partners = partners

    def list_partners(self, firm_domain: str) -> list[Partner]:
        return list(self.partners)


class FakeLinkedInCollector(LinkedInCollector):
    def __init__(self, posts_by_url: dict[str, list[dict]]) -> None:
        self.posts_by_url = posts_by_url
        self.received_urls: list[list[str]] = []

    def fetch_posts(self, profile_urls: Sequence[str], **kwargs) -> dict[str, list[dict]]:
        self.received_urls.append(list(profile_urls))
        return {u: self.posts_by_url.get(u, []) for u in profile_urls}


def make_partner(name: str, linkedin: str | None = None) -> Partner:
    return Partner(name=name, profile_url=f"https://example.com/{name}", linkedin_url=linkedin)
