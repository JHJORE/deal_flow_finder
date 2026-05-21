"""Composition root + CLI.

This is the *only* file allowed to import across all layers. Every wiring
decision lives here so that swapping a tool is a one-line edit. Running
``python -m pipeline.main run --phase 1`` is equivalent to importing the
matching script under ``scripts/`` — the scripts exist purely to give each
phase a CLI-discoverable filename.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer
from dotenv import load_dotenv

from pipeline.adapters.api.fastapi_routes import build_router
from pipeline.adapters.config.yaml_config_adapter import YamlConfigRepository
from pipeline.adapters.filings.edgar_adapter import EdgarFilingFetcher
from pipeline.adapters.linkedin.proxycurl_adapter import ProxycurlLinkedInFetcher
from pipeline.adapters.social.twitter_api_io_adapter import TwitterApiIoSocialFetcher
from pipeline.adapters.storage.json_repository import JsonFileRepository
from pipeline.adapters.web.firecrawl_adapter import FirecrawlWebFetcher
from pipeline.application.ports.config import ConfigRepository
from pipeline.application.use_cases.collect_blog_content import CollectBlogContent
from pipeline.application.use_cases.collect_linkedin_profiles import (
    CollectLinkedInProfiles,
)
from pipeline.application.use_cases.collect_social_activity import (
    CollectSocialActivity,
)
from pipeline.application.use_cases.crawl_firm_site import CrawlFirmSite
from pipeline.application.use_cases.discover_handles import DiscoverHandles
from pipeline.application.use_cases.query_edgar_filings import QueryEdgarFilings
from pipeline.application.use_cases.reconcile_portfolio_with_filings import (
    ReconcilePortfolioWithFilings,
)
from pipeline.entities.errors import ValidationError
from pipeline.entities.models import (
    BlogPost,
    Company,
    Filing,
    Firm,
    Partner,
    WatchlistEntry,
)
from pipeline.entities.value_objects import Handle, Url

logger = logging.getLogger("pipeline")

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
CONFIG_DIR = REPO_ROOT / "config"


# --------------------------------------------------------------------------- #
# Wiring
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Container:
    """Built lazily so a single missing key doesn't block every command."""

    repo: JsonFileRepository
    firms: list[Firm]
    overrides: dict[str, str]
    watchlist: list[WatchlistEntry]


def build_container() -> Container:
    load_dotenv(REPO_ROOT / ".env", override=False)
    repo = JsonFileRepository(DATA_DIR)
    config: ConfigRepository = YamlConfigRepository(
        firms_path=CONFIG_DIR / "firms.yaml",
        watchlist_path=CONFIG_DIR / "watchlist.yaml",
        handle_overrides_path=CONFIG_DIR / "handle_overrides.yaml",
    )
    return Container(
        repo=repo,
        firms=config.load_firms(),
        overrides=config.load_handle_overrides(),
        watchlist=config.load_watchlist(),
    )


def _build_web_fetcher() -> FirecrawlWebFetcher:
    from pipeline.frameworks.firecrawl_client import build_firecrawl_client

    return FirecrawlWebFetcher(build_firecrawl_client())


def _build_social_fetcher() -> TwitterApiIoSocialFetcher:
    from pipeline.frameworks.twitter_api_io_client import build_twitter_api_io_client

    return TwitterApiIoSocialFetcher(build_twitter_api_io_client())


def _build_linkedin_fetcher() -> ProxycurlLinkedInFetcher:
    from pipeline.frameworks.proxycurl_client import build_proxycurl_client

    return ProxycurlLinkedInFetcher(build_proxycurl_client(), DATA_DIR / "linkedin" / "_cache")


def _build_filing_fetcher() -> EdgarFilingFetcher:
    from pipeline.frameworks.edgar_client import build_edgar_client

    return EdgarFilingFetcher(build_edgar_client())


# --------------------------------------------------------------------------- #
# Phase runners (importable from scripts/ as well)
# --------------------------------------------------------------------------- #


def run_phase_1(container: Container) -> dict[str, Any]:
    """Crawl every firm and persist the merged firm graph."""
    web = _build_web_fetcher()
    use_case = CrawlFirmSite(web=web)
    all_partners: list[Partner] = []
    all_companies: list[Company] = []
    all_blog_posts: list[BlogPost] = []
    for firm in container.firms:
        logger.info("Phase 1: crawling %s", firm.name.value)
        subgraph = use_case.execute(firm)
        all_partners.extend(subgraph.partners)
        all_companies.extend(subgraph.companies)
        all_blog_posts.extend(subgraph.blog_posts)

    payload = {
        "partners": [_serialise_partner(p) for p in all_partners],
        "companies": [_serialise_company(c) for c in all_companies],
        "blog_posts": [_serialise_blog_post(b) for b in all_blog_posts],
    }
    container.repo.save("firm_graph", payload)
    return {
        "partners": len(all_partners),
        "companies": len(all_companies),
        "blog_posts": len(all_blog_posts),
    }


def run_phase_2(container: Container) -> dict[str, Any]:
    """Query EDGAR for Form D filings and reconcile against the portfolio."""
    fetcher = _build_filing_fetcher()
    query = QueryEdgarFilings(filings=fetcher)
    reconciliation = ReconcilePortfolioWithFilings()

    aliases: list[str] = []
    for firm in container.firms:
        aliases.extend(firm.edgar_aliases)
    filings = query.execute(aliases)

    graph = container.repo.load("firm_graph") or {}
    companies = _hydrate_companies(graph.get("companies", []) if isinstance(graph, dict) else [])
    result = reconciliation.execute(filings, companies)

    payload = {
        "disclosed": [_serialise_filing(f, disclosed=True) for f in result.disclosed],
        "undisclosed": [_serialise_filing(f, disclosed=False) for f in result.undisclosed],
    }
    container.repo.save("filings", payload)
    return {"disclosed": len(result.disclosed), "undisclosed": len(result.undisclosed)}


def run_phase_3(container: Container) -> dict[str, Any]:
    """Collect per-entity social, LinkedIn, and blog content."""
    graph = container.repo.load("firm_graph") or {}
    partners = _hydrate_partners(graph.get("partners", []) if isinstance(graph, dict) else [])

    handle_discovery = DiscoverHandles(overrides=container.overrides)
    resolved = handle_discovery.execute(partners, [])
    handles = [p.x_handle for p in resolved.partners if p.x_handle is not None]
    linkedin_urls = [p.linkedin_url for p in resolved.partners if p.linkedin_url is not None]
    linkedin_urls.extend(entry.linkedin_url for entry in container.watchlist)

    social = CollectSocialActivity(social=_build_social_fetcher(), repo=container.repo)
    linkedin = CollectLinkedInProfiles(linkedin=_build_linkedin_fetcher(), repo=container.repo)
    blog = CollectBlogContent(web=_build_web_fetcher(), repo=container.repo)

    social_results = social.execute(handles)
    linkedin_results = linkedin.execute(linkedin_urls)
    blog_posts = [
        _hydrate_blog_post(p)
        for p in (graph.get("blog_posts", []) if isinstance(graph, dict) else [])
    ]
    blog_results = blog.execute([p for p in blog_posts if p is not None])

    return {
        "handles": len(handles),
        "social_collected": len(social_results),
        "linkedin_collected": len(linkedin_results),
        "blog_posts_collected": len(blog_results),
        "unresolved_handles": list(resolved.unresolved_names),
    }


# --------------------------------------------------------------------------- #
# Serialisation helpers (matched by the frontend's TypeScript types)
# --------------------------------------------------------------------------- #


def _serialise_partner(p: Partner) -> dict[str, Any]:
    return {
        "id": p.id,
        "name": p.name,
        "firm": p.firm.value,
        "role": p.role,
        "x_handle": p.x_handle.value if p.x_handle else None,
        "linkedin_url": p.linkedin_url.value if p.linkedin_url else None,
        "blog_url": p.blog_url.value if p.blog_url else None,
        "bio": p.bio,
    }


def _serialise_company(c: Company) -> dict[str, Any]:
    return {
        "id": c.id,
        "name": c.name,
        "website": c.website.value if c.website else None,
        "sector": c.sector.value if c.sector else None,
        "stage": c.stage.value,
        "invested_by": [f.value for f in c.invested_by],
        "founder_ids": list(c.founder_ids),
        "description": c.description,
        "linkedin_company_url": c.linkedin_company_url.value if c.linkedin_company_url else None,
    }


def _serialise_blog_post(b: BlogPost) -> dict[str, Any]:
    return {
        "id": b.id,
        "author_partner_id": b.author_partner_id,
        "title": b.title,
        "body": b.body,
        "published_at": b.published_at.iso(),
        "source_url": b.source_url.value,
    }


def _serialise_filing(f: Filing, *, disclosed: bool) -> dict[str, Any]:
    return {
        "cik": f.cik.value,
        "issuer_name": f.issuer_name,
        "raise_amount": f.raise_amount,
        "named_investors": list(f.named_investors),
        "filing_date": f.filing_date.iso(),
        "form_type": f.form_type,
        "accession_number": f.accession_number,
        "source_url": f.source_url.value,
        "disclosed_in_portfolio": disclosed,
    }


def _hydrate_partners(items: list[Any]) -> list[Partner]:
    from pipeline.entities.value_objects import FirmName

    out: list[Partner] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        try:
            out.append(
                Partner(
                    id=str(raw["id"]),
                    name=str(raw["name"]),
                    firm=FirmName(raw["firm"]),
                    role=str(raw.get("role", "")),
                    x_handle=Handle(raw["x_handle"]) if raw.get("x_handle") else None,
                    linkedin_url=Url(raw["linkedin_url"]) if raw.get("linkedin_url") else None,
                    blog_url=Url(raw["blog_url"]) if raw.get("blog_url") else None,
                    bio=str(raw.get("bio", "")),
                )
            )
        except (KeyError, ValueError, ValidationError):
            continue
    return out


def _hydrate_companies(items: list[Any]) -> list[Company]:
    from pipeline.entities.value_objects import FirmName, Sector, Stage

    out: list[Company] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        try:
            out.append(
                Company(
                    id=str(raw["id"]),
                    name=str(raw["name"]),
                    website=Url(raw["website"]) if raw.get("website") else None,
                    sector=Sector(raw["sector"]) if raw.get("sector") else None,
                    stage=Stage(raw.get("stage", "unknown")),
                    invested_by=tuple(FirmName(f) for f in raw.get("invested_by", [])),
                    founder_ids=tuple(raw.get("founder_ids", [])),
                    description=str(raw.get("description", "")),
                    linkedin_company_url=(
                        Url(raw["linkedin_company_url"])
                        if raw.get("linkedin_company_url")
                        else None
                    ),
                )
            )
        except (KeyError, ValueError, ValidationError):
            continue
    return out


def _hydrate_blog_post(raw: Any) -> BlogPost | None:
    from pipeline.entities.value_objects import Timestamp

    if not isinstance(raw, dict):
        return None
    try:
        return BlogPost(
            id=str(raw["id"]),
            author_partner_id=str(raw.get("author_partner_id", "")),
            title=str(raw.get("title", "")),
            body=str(raw.get("body", "")),
            published_at=Timestamp.from_iso(raw["published_at"]),
            source_url=Url(raw["source_url"]),
        )
    except (KeyError, ValueError, ValidationError):
        return None


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


app = typer.Typer(add_completion=False, help="LAUNCH deal-flow pipeline.")


@app.command()
def run(
    phase: int = typer.Option(..., "--phase", "-p", help="Pipeline phase to run (1, 2, or 3)."),
) -> None:
    """Run a single pipeline phase."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    container = build_container()
    runners = {1: run_phase_1, 2: run_phase_2, 3: run_phase_3}
    if phase not in runners:
        raise typer.BadParameter(f"phase must be 1, 2, or 3 (got {phase})")
    result = runners[phase](container)
    typer.echo(f"Phase {phase} complete: {result}")


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start the FastAPI server."""
    import uvicorn
    from fastapi import FastAPI

    container = build_container()
    fastapi_app = FastAPI(title="LAUNCH deal-flow API")
    fastapi_app.include_router(build_router(container.repo))
    uvicorn.run(fastapi_app, host=host, port=port)


if __name__ == "__main__":
    app()
