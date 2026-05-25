from _fakes import FakeLinkedInCollector
from deal_flow.application.use_cases.enrich_firm_portfolio_with_linkedin import (
    EnrichPortfolioCompaniesWithLinkedIn,
    EnrichPortfolioCompaniesWithLinkedInInput,
)
from deal_flow.domain.entities.portfolio_company import PortfolioCompany


def test_enriches_only_companies_with_linkedin_url():
    companies = [
        PortfolioCompany(
            name="Acme", detail_url="", linkedin_url="https://linkedin.com/company/acme"
        ),
        PortfolioCompany(name="NoLI", detail_url="", linkedin_url=None),
    ]
    collector = FakeLinkedInCollector(
        {"https://linkedin.com/company/acme": [{"id": "p1"}]}
    )

    out = EnrichPortfolioCompaniesWithLinkedIn(collector).execute(
        EnrichPortfolioCompaniesWithLinkedInInput(companies=companies)
    )

    assert collector.received_urls == [["https://linkedin.com/company/acme"]]
    assert out[0].linkedin.posts[0].id == "p1"
    assert out[1].linkedin is None
