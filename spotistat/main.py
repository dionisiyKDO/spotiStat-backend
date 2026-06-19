"""FastAPI application entry point."""

from fastapi import FastAPI

from spotistat.api import stats
from spotistat.db.session import init_db

app = FastAPI(title="SpotiStat API", version="0.1.0")
init_db()

app.include_router(stats.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
