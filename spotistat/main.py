"""FastAPI application factory."""

from fastapi import FastAPI

from spotistat.db.session import init_db


def create_app() -> FastAPI:
    app = FastAPI(title="SpotiStat API", version="0.1.0")

    init_db()

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # Routers (history, stats, admin) are wired in subsequent steps.
    return app


app = create_app()
