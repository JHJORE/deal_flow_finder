"""Regression tests for the firm extractors.

The bug that motivated these tests: the original per-partner handle/linkedin
regex searched the whole page, so every partner ended up sharing the first
handle found. ``_section_chunks`` scopes the search to the markdown between
one heading and the next, which is what these tests pin down.
"""

from __future__ import annotations

from pipeline.application.use_cases.firm_extractors.sequoia import SequoiaExtractor
from pipeline.application.use_cases.firm_extractors.yc import YCExtractor
from pipeline.entities.value_objects import Handle, Url


def test_per_partner_handle_and_linkedin_are_scoped_not_global() -> None:
    markdown = """
## Roelof Botha

https://x.com/roelofbotha
https://linkedin.com/in/roelofbotha

## Alfred Lin

https://x.com/Alfred_Lin
https://linkedin.com/in/alfredlin
"""
    partners = SequoiaExtractor().extract_partners(markdown, Url("https://sequoiacap.com/people"))
    by_name = {p.name: p for p in partners}
    assert by_name["Roelof Botha"].x_handle == Handle("roelofbotha")
    assert by_name["Alfred Lin"].x_handle == Handle("Alfred_Lin")
    assert by_name["Roelof Botha"].linkedin_url == Url("https://linkedin.com/in/roelofbotha")
    assert by_name["Alfred Lin"].linkedin_url == Url("https://linkedin.com/in/alfredlin")


def test_partner_without_handle_gets_none_not_a_neighbor_handle() -> None:
    markdown = """
## Roelof Botha

https://x.com/roelofbotha

## Mystery Partner

bio without socials
"""
    partners = SequoiaExtractor().extract_partners(markdown, Url("https://sequoiacap.com/people"))
    mystery = next(p for p in partners if p.name == "Mystery Partner")
    assert mystery.x_handle is None
    assert mystery.linkedin_url is None


def test_companies_drop_obvious_navigation_links() -> None:
    markdown = "[About](https://example.com/about)\n[Stripe](https://stripe.com)\n[Twitter](https://twitter.com/x)\n[Klarna](https://klarna.com)\n"
    companies = YCExtractor().extract_companies(
        markdown, Url("https://www.ycombinator.com/companies")
    )
    names = {c.name for c in companies}
    assert names == {"Stripe", "Klarna"}
