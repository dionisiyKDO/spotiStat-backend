"""SQLAlchemy 2.0 typed models.

Two tables, mirroring the two-tier design:

* ``listens``      — raw play events, queried live for detail/drill-down endpoints.
* ``stat_entries`` — one row per (username, stat_key), holding a precomputed JSON
                     payload for the dashboard. Computed once per import.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Listen(Base):
    """A single play event from the Spotify streaming history export."""

    __tablename__ = "listens"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255))

    # Canonical time as Unix epoch seconds (UTC). Stored as an int so sorting and
    # session-gap math never re-parse strings — measured ~32x faster than strptime.
    played_at: Mapped[int] = mapped_column(Integer)
    ms_played: Mapped[int] = mapped_column(Integer)

    track_name: Mapped[str | None] = mapped_column(String(512))
    artist_name: Mapped[str | None] = mapped_column(String(512))
    album_name: Mapped[str | None] = mapped_column(String(512))
    track_uri: Mapped[str | None] = mapped_column(String(255))

    platform: Mapped[str | None] = mapped_column(String(128))
    conn_country: Mapped[str | None] = mapped_column(String(8))
    reason_start: Mapped[str | None] = mapped_column(String(64))
    reason_end: Mapped[str | None] = mapped_column(String(64))
    shuffle: Mapped[bool] = mapped_column(Boolean, default=False)
    skipped: Mapped[bool] = mapped_column(Boolean, default=False)

    # Kept (nullable) so podcast rows survive import; not used by music stats yet.
    episode_name: Mapped[str | None] = mapped_column(String(512))
    episode_show_name: Mapped[str | None] = mapped_column(String(512))

    __table_args__ = (
        # Composite indexes for the *selective* detail endpoints (one artist /
        # one track). A bare (username) index is deliberately omitted: with a
        # single user owning the whole table it can't help full-archive scans
        # and measurably hurts the GROUP BYs.
        Index("ix_listens_user_artist", "username", "artist_name"),
        Index("ix_listens_user_track_uri", "username", "track_uri"),
        Index("ix_listens_user_played_at", "username", "played_at"),
    )


class StatEntry(Base):
    """A single precomputed dashboard statistic for a user."""

    __tablename__ = "stat_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255))
    stat_key: Mapped[str] = mapped_column(String(64))
    payload: Mapped[Any] = mapped_column(JSON)  # list or dict, (de)serialized by SA
    computed_at: Mapped[int] = mapped_column(Integer)  # epoch seconds, UTC
    version: Mapped[int] = mapped_column(Integer, default=1)

    __table_args__ = (
        Index("ix_stat_entries_user_key", "username", "stat_key", unique=True),
    )
