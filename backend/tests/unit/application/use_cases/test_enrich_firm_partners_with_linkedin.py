from _fakes import (
    FakeLinkedInCollector,
    FakePartnerDirectory,
    make_partner,
)
from deal_flow.application.use_cases.enrich_firm_partners_with_linkedin import (
    EnrichFirmPartnersWithLinkedIn,
    EnrichFirmPartnersWithLinkedInInput,
    handle_from_linkedin_url,
)


def test_enriches_only_partners_with_linkedin_url():
    directory = FakePartnerDirectory(
        [
            make_partner("Alice", "https://linkedin.com/in/alice"),
            make_partner("Bob", None),
        ]
    )
    collector = FakeLinkedInCollector(
        {"https://linkedin.com/in/alice": [{"id": "p1"}]}
    )

    out = EnrichFirmPartnersWithLinkedIn(directory, collector).execute(
        EnrichFirmPartnersWithLinkedInInput(firm_domain="x.com")
    )

    assert collector.received_urls == [["https://linkedin.com/in/alice"]]
    assert out[0].linkedin.posts[0].id == "p1"
    assert out[1].linkedin is None


def test_handle_from_linkedin_url():
    assert handle_from_linkedin_url("https://www.linkedin.com/in/immerman/") == "immerman"
    assert handle_from_linkedin_url("https://linkedin.com/in/Foo-Bar") == "foo-bar"
    assert handle_from_linkedin_url("https://linkedin.com/company/a16z") is None
    assert handle_from_linkedin_url(None) is None
