from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from pipeline.adapters.api.fastapi_routes import build_router
from pipeline.tests.application.fakes import FakeRepository


def _client(repo: FakeRepository) -> TestClient:
    app = FastAPI()
    app.include_router(build_router(repo))
    return TestClient(app)


def test_health() -> None:
    assert _client(FakeRepository()).get("/health").json() == {"status": "ok"}


def test_digest_returns_payload() -> None:
    repo = FakeRepository()
    repo.save("digest", {"cards": [], "generated_at": "2024-01-01"})
    resp = _client(repo).get("/digest")
    assert resp.status_code == 200
    assert resp.json()["generated_at"] == "2024-01-01"


def test_digest_404_when_missing() -> None:
    assert _client(FakeRepository()).get("/digest").status_code == 404


def test_partner_lookup() -> None:
    repo = FakeRepository()
    repo.save(
        "firm_graph",
        {"partners": [{"name": "Roelof Botha", "firm": "sequoia"}], "companies": []},
    )
    resp = _client(repo).get("/partners/roelof-botha")
    assert resp.status_code == 200
    assert resp.json()["firm"] == "sequoia"


def test_company_lookup_404() -> None:
    repo = FakeRepository()
    repo.save("firm_graph", {"companies": [], "partners": []})
    assert _client(repo).get("/companies/missing").status_code == 404
