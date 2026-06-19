"""Engine, session factory, and a FastAPI dependency for handing out sessions."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from spotistat.config import get_settings

settings = get_settings()

# check_same_thread=False: FastAPI runs sync (`def`) endpoints in a threadpool,
# so a connection may be touched from a different thread than it was created on.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create tables if they don't exist. Called explicitly (never on import)."""
    from spotistat.db import models  # local import keeps this module side-effect free

    models.Base.metadata.create_all(engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
