from fastapi import FastAPI

app = FastAPI(title="deal_flow")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
