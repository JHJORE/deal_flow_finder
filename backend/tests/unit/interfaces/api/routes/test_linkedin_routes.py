from fastapi.testclient import TestClient

from _fakes import FakeLinkedInCollector, FakePartnerDirectory, make_partner
from deal_flow.application.ports.repositories.partner_directory import (
    PartnerDirectory,
)
from deal_flow.application.use_cases.analyze_partner_linkedin_signals import (
    AnalyzePartnerLinkedInSignals,
)
from deal_flow.application.use_cases.enrich_firm_partners_with_linkedin import (
    EnrichFirmPartnersWithLinkedIn,
)
from deal_flow.application.use_cases.enrich_firm_portfolio_with_linkedin import (
    EnrichPortfolioCompaniesWithLinkedIn,
)
from deal_flow.domain.entities.linkedin.linkedin_analysis import LinkedInAnalysis
from deal_flow.domain.entities.linkedin.linkedin_snapshot import LinkedInSnapshot
from deal_flow.domain.entities.partner import Partner
from deal_flow.domain.entities.portfolio_company import PortfolioCompany
from deal_flow.infrastructure.persistence.output_store import OutputStore
from deal_flow.interfaces.api.app import app
from deal_flow.interfaces.api.dependencies import (
    get_analyze_partner_linkedin_signals,
    get_enrich_firm_partners_with_linkedin,
    get_enrich_portfolio_companies_with_linkedin,
    get_extract_firm_portfolio,
    get_output_store,
)


class _NoopAnalyzer(AnalyzePartnerLinkedInSignals):
    """Stand-in for the LLM-backed analyzer in route tests that aren't
    exercising analysis behaviour. Returns a deterministic empty analysis
    so the route's persist+respond path still runs."""

    def __init__(self) -> None:  # noqa: D401  — stub
        pass

    def execute(self, snapshot: LinkedInSnapshot) -> LinkedInAnalysis:
        from datetime import UTC, datetime

        return LinkedInAnalysis(
            general_theme="",
            topics=(),
            item_themes=(),
            analyzed_at=datetime.now(UTC),
        )


class _NoopStore(OutputStore):
    def __init__(self) -> None:
        pass

    def write(self, payload, *parts):  # type: ignore[override]
        return None


def _override(overrides: dict) -> TestClient:
    app.dependency_overrides[get_output_store] = lambda: _NoopStore()
    # Default the LinkedIn analyzer to a no-op so existing tests aren't
    # forced to wire the LLM port. Tests that exercise analysis behaviour
    # can override this key explicitly.
    app.dependency_overrides[get_analyze_partner_linkedin_signals] = (
        lambda: _NoopAnalyzer()
    )
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
            r = client.get("/firms/a16z.com/partners/linkedin")
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
            r = client.get("/firms/unknown.example/partners/linkedin")
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
            r = client.get("/firms/a16z.com/partners/alice/linkedin")
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
            r = client.get("/firms/a16z.com/partners/nobody/linkedin")
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
            r = client.get("/firms/a16z.com/portfolio/linkedin")
        assert r.status_code == 200
        body = r.json()
        assert body[0]["linkedin"]["posts"][0]["id"] == "p1"
        assert body[1]["linkedin"] is None
    finally:
        app.dependency_overrides.clear()
