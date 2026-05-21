from __future__ import annotations

from pipeline.application.use_cases.crawl_firm_site import CrawlFirmSite
from pipeline.entities.models import Firm
from pipeline.entities.value_objects import FirmName, Url
from pipeline.tests.application.fakes import FakeWebFetcher


def _firm() -> Firm:
    return Firm(
        name=FirmName.SEQUOIA,
        website=Url("https://sequoiacap.com"),
        people_page_url=Url("https://sequoiacap.com/people"),
        portfolio_page_url=Url("https://sequoiacap.com/companies"),
        blog_url=Url("https://sequoiacap.com/perspective"),
        edgar_aliases=("Sequoia Capital",),
    )


def test_crawl_extracts_partners_and_companies() -> None:
    web = FakeWebFetcher(
        pages={
            "https://sequoiacap.com/people": "## Roelof Botha\n\n## Alfred Lin\n",
            "https://sequoiacap.com/companies": "[Stripe](https://stripe.com)\n[Klarna](https://klarna.com)\n",
            "https://sequoiacap.com/perspective": "[The Evolution of Founder-Mode](https://sequoiacap.com/article/founder-mode)\n",
        }
    )
    result = CrawlFirmSite(web=web).execute(_firm())
    assert {p.name for p in result.partners} == {"Roelof Botha", "Alfred Lin"}
    assert {c.name for c in result.companies} == {"Stripe", "Klarna"}
    assert len(result.blog_posts) == 1


def test_crawl_survives_blog_fetch_failure() -> None:
    web = FakeWebFetcher(
        pages={
            "https://sequoiacap.com/people": "## Roelof Botha\n",
            "https://sequoiacap.com/companies": "[Stripe](https://stripe.com)\n",
        },
        fail_urls={"https://sequoiacap.com/perspective"},
    )
    result = CrawlFirmSite(web=web).execute(_firm())
    assert result.partners
    assert result.blog_posts == ()
