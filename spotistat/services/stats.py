"""Compute and persist the precomputed dashboard statistics for a user.

Every stat is derived from a single in-memory pass over the user's listens, then
stored as one ``StatEntry`` row per stat. Recompute only runs on import (rare), so
this favours readable, self-contained functions over squeezing out milliseconds.
"""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from spotistat.config import get_settings
from spotistat.db.models import Listen, StatEntry

MS_IN_MINUTE = 60_000
MS_IN_HOUR = 3_600_000
MS_IN_DAY = 86_400_000

TOP_LIMIT = 50
SESSION_GAP_SECONDS = 30 * 60

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# --- public API ---------------------------------------------------------------


def recompute(db: Session, username: str) -> int:
    """Calculate every stat for a user and persist it. Returns computed_at (epoch)."""
    tz = ZoneInfo(get_settings().timezone)
    return save_stats(db, username, calculate_all(db, username, tz))


def load_dashboard(db: Session, username: str) -> dict[str, Any] | None:
    """The full precomputed bundle for a user, or ``None`` if not computed yet."""
    rows = db.scalars(select(StatEntry).where(StatEntry.username == username)).all()
    if not rows:
        return None
    return {
        "username": username,
        "computed_at": rows[0].computed_at,
        "stats": {row.stat_key: row.payload for row in rows},
    }


def save_stats(db: Session, username: str, stats: dict[str, Any]) -> int:
    """Replace a user's stored stats with a fresh set (one row per stat)."""
    now = int(time.time())
    db.execute(delete(StatEntry).where(StatEntry.username == username))
    db.execute(
        insert(StatEntry),
        [
            {"username": username, "stat_key": key, "payload": payload, "computed_at": now}
            for key, payload in stats.items()
        ],
    )
    db.commit()
    return now


# --- calculation --------------------------------------------------------------


def calculate_all(db: Session, username: str, tz: ZoneInfo) -> dict[str, Any]:
    rows = db.execute(
        select(
            Listen.played_at,
            Listen.ms_played,
            Listen.artist_name,
            Listen.track_name,
            Listen.track_uri,
            Listen.platform,
            Listen.reason_end,
            Listen.skipped,
        )
        .where(Listen.username == username)
        .order_by(Listen.played_at)
    ).all()

    return {
        "total_listening_time": _total_listening_time(rows),
        "unique_tracks_count": _unique_tracks_count(rows),
        "skip_stats": _skip_stats(rows),
        "most_skipped_tracks": _most_skipped_tracks(rows),
        "end_reasons": _end_reasons(rows),
        "platform_stats": _platform_stats(rows),
        "top_artists": _top_artists(rows),
        "top_tracks": _top_tracks(rows),
        "longest_session": _longest_session(rows),
        **_time_breakdowns(rows, tz),
    }


def _total_listening_time(rows) -> dict:
    total = sum(r.ms_played or 0 for r in rows)
    return {
        "total_listening_ms": total,
        "total_listening_minutes": round(total / MS_IN_MINUTE, 2),
        "total_listening_hours": round(total / MS_IN_HOUR, 2),
        "total_listening_days": round(total / MS_IN_DAY, 2),
    }


def _unique_tracks_count(rows) -> dict:
    return {"unique_tracks_count": len({r.track_uri for r in rows if r.track_uri})}


def _skip_stats(rows) -> dict:
    total = len(rows)
    skipped = sum(1 for r in rows if r.skipped)
    return {
        "total_plays": total,
        "skipped_tracks": skipped,
        "skip_rate": skipped / total if total else 0,
        "skip_percentage": skipped / total * 100 if total else 0,
    }


def _most_skipped_tracks(rows, limit: int = TOP_LIMIT) -> list:
    counts: dict[tuple, int] = defaultdict(int)
    uris: dict[tuple, str | None] = {}
    for r in rows:
        if r.skipped and r.track_name:  # skip podcast/null-name rows
            key = (r.track_name, r.artist_name)
            counts[key] += 1
            uris.setdefault(key, r.track_uri)
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    return [
        {"track_name": name, "artist": artist, "skip_count": count,
         "spotify_track_uri": uris[(name, artist)]}
        for (name, artist), count in ranked
    ]


def _end_reasons(rows) -> list:
    counts: dict[str | None, int] = defaultdict(int)
    for r in rows:
        counts[r.reason_end] += 1
    return [
        {"reason_end": reason, "count": count}
        for reason, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    ]


def _platform_stats(rows) -> list:
    groups = {name: [0, 0] for name in ("Linux", "Windows", "Android", "Other")}
    for r in rows:
        name = (r.platform or "").lower()
        if "linux" in name:
            bucket = groups["Linux"]
        elif "windows" in name:
            bucket = groups["Windows"]
        elif "android" in name:
            bucket = groups["Android"]
        else:
            bucket = groups["Other"]
        bucket[0] += 1
        bucket[1] += r.ms_played or 0
    return [
        {"platform": name, "play_count": plays, "total_ms_played": ms}
        for name, (plays, ms) in groups.items()
    ]


def _top_artists(rows, limit: int = TOP_LIMIT) -> list:
    plays: dict[str, int] = defaultdict(int)
    ms: dict[str, int] = defaultdict(int)
    tracks: dict[str, set] = defaultdict(set)
    for r in rows:
        if not r.artist_name:
            continue
        plays[r.artist_name] += 1
        ms[r.artist_name] += r.ms_played or 0
        if r.track_name:
            tracks[r.artist_name].add(r.track_name)
    return [
        {"artist": artist, "play_count": plays[artist], "total_ms_played": ms[artist],
         "total_hours": round(ms[artist] / MS_IN_HOUR, 2),
         "distinct_track_count": len(tracks[artist])}
        for artist in sorted(ms, key=ms.get, reverse=True)[:limit]
    ]


def _top_tracks(rows, limit: int = TOP_LIMIT) -> list:
    plays: dict[tuple, int] = defaultdict(int)
    ms: dict[tuple, int] = defaultdict(int)
    uris: dict[tuple, str | None] = {}
    for r in rows:
        if not r.track_name:
            continue
        key = (r.track_name, r.artist_name)
        plays[key] += 1
        ms[key] += r.ms_played or 0
        uris.setdefault(key, r.track_uri)
    return [
        {"track_name": name, "artist": artist, "play_count": plays[(name, artist)],
         "total_ms_played": ms[(name, artist)],
         "total_hours": round(ms[(name, artist)] / MS_IN_HOUR, 2),
         "spotify_track_uri": uris[(name, artist)]}
        for (name, artist) in sorted(ms, key=ms.get, reverse=True)[:limit]
    ]


def _longest_session(rows, gap_seconds: int = SESSION_GAP_SECONDS) -> dict:
    """Longest gap-delimited session, by total ms played. Times are epoch seconds."""
    best: dict | None = None
    current: list = []
    current_ms = 0
    prev: int | None = None

    for r in rows:
        if prev is not None and r.played_at - prev > gap_seconds:
            best = _keep_longer(best, current, current_ms)
            current, current_ms = [], 0
        current.append({
            "track_name": r.track_name,
            "artist": r.artist_name,
            "track_uri": r.track_uri,
            "played_at": r.played_at,
            "ms_played": r.ms_played or 0,
        })
        current_ms += r.ms_played or 0
        prev = r.played_at

    return _keep_longer(best, current, current_ms) or {}


def _keep_longer(best: dict | None, tracks: list, total_ms: int) -> dict | None:
    if not tracks:
        return best
    if best is None or total_ms > best["total_ms_played"]:
        return {
            "session_start": tracks[0]["played_at"],
            "session_end": tracks[-1]["played_at"],
            "total_tracks": len(tracks),
            "total_ms_played": total_ms,
            "tracks": tracks,
        }
    return best


def _time_breakdowns(rows, tz: ZoneInfo) -> dict:
    """All time-bucketed stats in one pass, bucketed in the configured local tz."""
    by_hour: dict[int, list] = defaultdict(lambda: [0, 0])
    by_weekday: dict[int, list] = defaultdict(lambda: [0, 0])
    by_month: dict[str, list] = defaultdict(lambda: [0, 0])
    by_year: dict[int, list] = defaultdict(lambda: [0, 0])
    by_date: dict[str, list] = defaultdict(lambda: [0, 0])

    for r in rows:
        dt = datetime.fromtimestamp(r.played_at, tz)
        ms = r.ms_played or 0
        for bucket, key in (
            (by_hour, dt.hour),
            (by_weekday, dt.weekday()),  # Monday = 0
            (by_month, f"{dt.year:04d}-{dt.month:02d}"),
            (by_year, dt.year),
            (by_date, dt.date().isoformat()),
        ):
            bucket[key][0] += 1
            bucket[key][1] += ms

    return {
        "listening_by_hour": [
            {"hour": h, "play_count": by_hour[h][0], "total_ms_played": by_hour[h][1]}
            for h in range(24)  # always 0..23, zero-filled
        ],
        "listening_by_weekday": [
            {"weekday": WEEKDAYS[d], "play_count": by_weekday[d][0],
             "total_ms_played": by_weekday[d][1]}
            for d in range(7)
        ],
        "listening_by_month": [
            {"month": month, "play_count": c, "total_ms_played": ms}
            for month, (c, ms) in sorted(by_month.items())
        ],
        "listening_by_year": [
            {"year": year, "play_count": c, "total_ms_played": ms}
            for year, (c, ms) in sorted(by_year.items())
        ],
        "listening_by_date": [
            {"date": date, "play_count": c, "total_ms_played": ms}
            for date, (c, ms) in sorted(by_date.items())
        ],
    }
