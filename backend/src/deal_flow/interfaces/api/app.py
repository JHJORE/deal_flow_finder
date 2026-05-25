from fastapi import FastAPI

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
