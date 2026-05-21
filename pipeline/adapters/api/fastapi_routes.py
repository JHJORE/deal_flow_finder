"""Read-only HTTP API for the Next.js frontend.

Mounted on FastAPI from ``pipeline.main``. Endpoints serve the contents of
``data/`` directly — there is no business logic here, only shaping. If a
frontend needs new fields, add a use case + repository call, not a SQL-style
join here.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from pipeline.application.ports.repository import EntityRepository


def build_router(repo: EntityRepository) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/digest")
    def digest() -> dict[str, Any]:
        payload = repo.load("digest")
        if payload is None:
            raise HTTPException(status_code=404, detail="digest not generated yet")
        return _ensure_dict(payload, "digest")

    @router.get("/firm-graph")
    def firm_graph() -> dict[str, Any]:
        payload = repo.load("firm_graph")
        if payload is None:
            raise HTTPException(status_code=404, detail="firm graph not generated yet")
        return _ensure_dict(payload, "firm_graph")

    @router.get("/filings")
    def filings() -> dict[str, Any]:
        payload = repo.load("filings")
        if payload is None:
            raise HTTPException(status_code=404, detail="filings not generated yet")
        return _ensure_dict(payload, "filings")

    @router.get("/partners/{slug}")
    def partner(slug: str) -> dict[str, Any]:
        graph = repo.load("firm_graph") or {}
        partners = graph.get("partners", []) if isinstance(graph, dict) else []
        for p in partners:
            if isinstance(p, dict) and _slugify(str(p.get("name", ""))) == slug:
                return p
        raise HTTPException(status_code=404, detail=f"partner {slug!r} not found")

    @router.get("/companies/{slug}")
    def company(slug: str) -> dict[str, Any]:
        graph = repo.load("firm_graph") or {}
        companies = graph.get("companies", []) if isinstance(graph, dict) else []
        for c in companies:
            if isinstance(c, dict) and _slugify(str(c.get("name", ""))) == slug:
                return c
        raise HTTPException(status_code=404, detail=f"company {slug!r} not found")

    return router


def _slugify(name: str) -> str:
    return "-".join(name.lower().split())


def _ensure_dict(payload: Any, key: str) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    raise HTTPException(status_code=500, detail=f"{key} payload is not a JSON object")
