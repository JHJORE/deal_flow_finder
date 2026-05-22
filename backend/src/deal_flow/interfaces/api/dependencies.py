"""Composition root.

This is the **only** module that may import from `deal_flow.infrastructure`.
Wire concrete adapters (infrastructure) to abstract ports (application) here,
and expose them as FastAPI `Depends(...)` providers consumed by route handlers.

Example pattern (uncomment when you have real ports + adapters):

    from functools import lru_cache
    from fastapi import Depends

    from deal_flow.application.ports.repositories.deal_repository import DealRepository
    from deal_flow.application.use_cases.find_deals import FindDeals
    from deal_flow.infrastructure.config.settings import Settings, get_settings
    from deal_flow.infrastructure.persistence.postgres_deal_repository import (
        PostgresDealRepository,
    )

    @lru_cache
    def get_deal_repository(settings: Settings = Depends(get_settings)) -> DealRepository:
        return PostgresDealRepository(dsn=settings.postgres_dsn)

    def get_find_deals(repo: DealRepository = Depends(get_deal_repository)) -> FindDeals:
        return FindDeals(deals=repo)
"""
