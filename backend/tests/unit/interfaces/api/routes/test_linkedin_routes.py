from _fakes import FakeLinkedInCollector, FakePartnerDirectory, make_partner
from fastapi.testclient import TestClient

from deal_flow.application.ports.repositories.partner_directory import (
    PartnerDirectory,
)
from deal_flow.application.use_cases.enrich_firm_partners_with_linkedin import (
    EnrichFirmPartnersWithLinkedIn,
)
from deal_flow.application.use_cases.enrich_firm_portfolio_with_linkedin import (
    EnrichPortfolioCompaniesWithLinkedIn,
)
from deal_flow.domain.entities.partner import Partner
from deal_flow.domain.entities.portfolio_company import PortfolioCompany
from deal_flow.infrastructure.persistence.output_store import OutputStore
from deal_flow.interfaces.api.app import app
from deal_flow.interfaces.api.dependencies import (
    get_enrich_firm_partners_with_linkedin,
    get_enrich_portfolio_companies_with_linkedin,
    get_extract_firm_portfolio,
    get_output_store,
)


class _NoopStore(OutputStore):
    def __init__(self) -> None:
        pass

    def write(self, payload, *parts):  # type: ignore[override]
        return None


def _override(overrides: dict) -> TestClient:
    app.dependency_overrides[get_output_store] = lambda: _NoopStore()
    for key, value in overrides.items():
        app.dependency_overrides[key] = lambda v=value: v
    return TestClient(app)


def _partners_uc(partners: list[Partner], posts: dict[str, list[dict]]):
    return EnrichFirmPartnersWithLinkedIn(
        FakePartnerDirectory(partners), FakeLinkedInCollector(posts)
    )


def test_batch_partners_route_enriches_and_returns():
    uc = _partners_uc(
        [make_partner("Alice", "https://linkedin.com/in/alice"), make_partner("Bob")],
        {"https://linkedin.com/in/alice": [{"id": "p1"}]},
    )
    try:
        with _override({get_enrich_firm_partners_with_linkedin: uc}) as client:
            r = client.get("/api/firms/a16z.com/partners/linkedin")
        assert r.status_code == 200
        body = r.json()
        assert body[0]["linkedin"]["posts"][0]["id"] == "p1"
        assert body[1]["linkedin"] is None
    finally:
        app.dependency_overrides.clear()


def test_batch_partners_route_404_when_directory_missing():
    class _Missing(PartnerDirectory):
        def list_partners(self, firm_domain):
            raise FileNotFoundError(f"no fixture for {firm_domain}")

    uc = EnrichFirmPartnersWithLinkedIn(_Missing(), FakeLinkedInCollector({}))
    try:
        with _override({get_enrich_firm_partners_with_linkedin: uc}) as client:
            r = client.get("/api/firms/unknown.example/partners/linkedin")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_single_partner_route_resolves_by_handle():
    uc = _partners_uc(
        [make_partner("Alice Wong", "https://linkedin.com/in/alice")],
        {"https://linkedin.com/in/alice": [{"id": "p1"}]},
    )
    try:
        with _override({get_enrich_firm_partners_with_linkedin: uc}) as client:
            r = client.get("/api/firms/a16z.com/partners/alice/linkedin")
        assert r.status_code == 200
        assert r.json()["name"] == "Alice Wong"
    finally:
        app.dependency_overrides.clear()


def test_single_partner_route_404_when_handle_unknown_and_no_apify_call():
    collector = FakeLinkedInCollector({})
    uc = EnrichFirmPartnersWithLinkedIn(
        FakePartnerDirectory([make_partner("Alice", "https://linkedin.com/in/alice")]),
        collector,
    )
    try:
        with _override({get_enrich_firm_partners_with_linkedin: uc}) as client:
            r = client.get("/api/firms/a16z.com/partners/nobody/linkedin")
        assert r.status_code == 404
        assert collector.received_urls == []
    finally:
        app.dependency_overrides.clear()


def test_portfolio_route_extracts_then_enriches():
    companies = [
        PortfolioCompany(
            name="Acme", detail_url="", linkedin_url="https://linkedin.com/company/acme"
        ),
        PortfolioCompany(name="NoLI", detail_url=""),
    ]

    class _FakeExtract:
        def execute(self, _input):
            return list(companies)

    enrich = EnrichPortfolioCompaniesWithLinkedIn(
        FakeLinkedInCollector({"https://linkedin.com/company/acme": [{"id": "p1"}]})
    )
    try:
        with _override(
            {
                get_extract_firm_portfolio: _FakeExtract(),
                get_enrich_portfolio_companies_with_linkedin: enrich,
            }
        ) as client:
            r = client.get("/api/firms/a16z.com/portfolio/linkedin")
        assert r.status_code == 200
        body = r.json()
        assert body[0]["linkedin"]["posts"][0]["id"] == "p1"
        assert body[1]["linkedin"] is None
    finally:
        app.dependency_overrides.clear()
