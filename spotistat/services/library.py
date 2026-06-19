"""Live (on-demand) queries for the artist/track drill-down pages.

These run against the raw ``listens`` table. Whole-library lists use SQL GROUP BY;
single-artist / single-track detail loads the (small, indexed) subset and buckets
its timeline in the local timezone — matching how the dashboard stats are computed.

All functions accept an optional ``start``/``end`` epoch range (end exclusive); the
``(username, played_at)`` index keeps the range selection cheap.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from spotistat.config import get_settings
from spotistat.constants import MS_IN_HOUR, MS_IN_MINUTE
from spotistat.db.models import Listen

MIN_MS = MS_IN_MINUTE * 10  # ignore artists/tracks with under 10 minutes total


def _tz() -> ZoneInfo:
    return ZoneInfo(get_settings().timezone)


def _apply_range(stmt, start: int | None, end: int | None):
    if start is not None:
        stmt = stmt.where(Listen.played_at >= start)
    if end is not None:
        stmt = stmt.where(Listen.played_at < end)
    return stmt


def list_artists(
    db: Session, username: str, *, start: int | None = None, end: int | None = None,
    limit: int | None = None,
) -> list[dict]:
    stmt = (
        select(
            Listen.artist_name,
            func.count(Listen.id).label("play_count"),
            func.sum(Listen.ms_played).label("total_ms"),
        )
        .where(Listen.username == username, Listen.artist_name.is_not(None))
        .group_by(Listen.artist_name)
        .having(func.sum(Listen.ms_played) > MIN_MS)
        .order_by(func.sum(Listen.ms_played).desc())
    )
    stmt = _apply_range(stmt, start, end)
    if limit:
        stmt = stmt.limit(limit)
    return [
        {
            "artist": r.artist_name,
            "play_count": r.play_count,
            "total_ms_played": r.total_ms or 0,
            "total_hours": round((r.total_ms or 0) / MS_IN_HOUR, 2),
        }
        for r in db.execute(stmt).all()
    ]


def list_tracks(
    db: Session, username: str, *, start: int | None = None, end: int | None = None,
    limit: int | None = None,
) -> list[dict]:
    stmt = (
        select(
            Listen.track_name,
            Listen.artist_name,
            func.count(Listen.id).label("play_count"),
            func.sum(Listen.ms_played).label("total_ms"),
            func.max(Listen.track_uri).label("track_uri"),
        )
        .where(Listen.username == username, Listen.track_name.is_not(None))
        .group_by(Listen.track_name, Listen.artist_name)
        .having(func.sum(Listen.ms_played) > MIN_MS)
        .order_by(func.sum(Listen.ms_played).desc())
    )
    stmt = _apply_range(stmt, start, end)
    if limit:
        stmt = stmt.limit(limit)
    return [
        {
            "track_name": r.track_name,
            "artist": r.artist_name,
            "play_count": r.play_count,
            "total_ms_played": r.total_ms or 0,
            "total_hours": round((r.total_ms or 0) / MS_IN_HOUR, 2),
            "spotify_track_uri": r.track_uri,
        }
        for r in db.execute(stmt).all()
    ]


def artist_tracks(
    db: Session, username: str, artist_name: str, *,
    start: int | None = None, end: int | None = None,
) -> list[dict]:
    stmt = (
        select(
            Listen.track_name,
            func.count(Listen.id).label("play_count"),
            func.sum(Listen.ms_played).label("total_ms"),
            func.max(Listen.track_uri).label("track_uri"),
        )
        .where(
            Listen.username == username,
            Listen.artist_name == artist_name,
            Listen.track_name.is_not(None),
        )
        .group_by(Listen.track_name)
        .order_by(func.sum(Listen.ms_played).desc())
    )
    stmt = _apply_range(stmt, start, end)
    return [
        {
            "track_name": r.track_name,
            "play_count": r.play_count,
            "total_ms_played": r.total_ms or 0,
            "total_hours": round((r.total_ms or 0) / MS_IN_HOUR, 2),
            "spotify_track_uri": r.track_uri,
        }
        for r in db.execute(stmt).all()
    ]


def artist_detail(
    db: Session, username: str, artist_name: str, *,
    start: int | None = None, end: int | None = None,
) -> dict | None:
    stmt = _apply_range(
        select(Listen.played_at, Listen.ms_played).where(
            Listen.username == username, Listen.artist_name == artist_name
        ),
        start, end,
    ).order_by(Listen.played_at)
    rows = db.execute(stmt).all()
    if not rows:
        return None
    return {"artist_name": artist_name, **_summarise(rows, _tz())}


def track_detail(
    db: Session, username: str, track_id: str, *,
    start: int | None = None, end: int | None = None,
) -> dict | None:
    track_uri = f"spotify:track:{track_id}"
    stmt = _apply_range(
        select(Listen.played_at, Listen.ms_played, Listen.reason_end).where(
            Listen.username == username, Listen.track_uri == track_uri
        ),
        start, end,
    ).order_by(Listen.played_at)
    rows = db.execute(stmt).all()
    if not rows:
        return None
    detail = _summarise(rows, _tz())
    # Estimated song length = the most common play length among natural finishes.
    # (Old code crashed here when a track had no 'trackdone' plays; now -> None.)
    finished = [r.ms_played for r in rows if r.reason_end == "trackdone" and r.ms_played]
    detail["song_length"] = Counter(finished).most_common(1)[0][0] if finished else None
    return {"track_id": track_id, **detail}


def _summarise(rows, tz: ZoneInfo) -> dict[str, Any]:
    """Shared totals + per-day timeline for a single artist or track."""
    total_ms = sum(r.ms_played or 0 for r in rows)
    total_plays = len(rows)

    by_date: dict[str, list] = defaultdict(lambda: [0, 0])
    for r in rows:
        day = datetime.fromtimestamp(r.played_at, tz).date().isoformat()
        by_date[day][0] += 1
        by_date[day][1] += r.ms_played or 0

    return {
        "total_ms_played": total_ms,
        "total_plays": total_plays,
        "total_hours": round(total_ms / MS_IN_HOUR, 2),
        "distinct_days_played": len(by_date),
        "first_played": rows[0].played_at,  # epoch seconds; frontend formats
        "last_played": rows[-1].played_at,
        "avg_playtime_per_play": total_ms / total_plays if total_plays else 0,
        "timeline": [
            {"date": day, "play_count": c, "total_ms_played": ms}
            for day, (c, ms) in sorted(by_date.items())
        ],
    }
