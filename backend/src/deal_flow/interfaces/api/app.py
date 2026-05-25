from pathlib import Path

from fastapi import FastAPI

from deal_flow.infrastructure.config.settings import _BACKEND_ROOT
from deal_flow.interfaces.api.routes.firms import router as firms_router
from deal_flow.interfaces.api.routes.partner_profiles import (
    router as partner_profiles_router,
)
from deal_flow.interfaces.api.routes.portfolio_profiles import (
    router as portfolio_profiles_router,
)

app = FastAPI(title="deal_flow")
app.include_router(firms_router)
app.include_router(partner_profiles_router)
app.include_router(portfolio_profiles_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/_debug/paths")
def debug_paths() -> dict:
    data_dir = _BACKEND_ROOT / "data"
    return {
        "cwd": str(Path.cwd()),
        "settings_file": str(Path(__file__).resolve()),
        "backend_root": str(_BACKEND_ROOT),
        "firms_yaml_exists": (_BACKEND_ROOT / "firms.yaml").exists(),
        "data_dir_exists": data_dir.exists(),
        "data_files": sorted(p.name for p in data_dir.iterdir()) if data_dir.exists() else [],
    }
