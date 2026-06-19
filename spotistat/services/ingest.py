"""Import Spotify "Extended Streaming History" JSON archives into ``listens``.

An import is idempotent per user: by default it replaces that user's existing
rows, so re-running it never produces duplicates (the old appender did).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete, insert
from sqlalchemy.orm import Session

from spotistat.db.models import Listen


def _to_epoch(ts: str) -> int:
    """Spotify timestamps look like ``2019-07-30T15:47:13Z`` (UTC).

    ``fromisoformat`` doesn't accept the ``Z`` suffix until Python 3.11, so we
    normalise it to ``+00:00`` first; this also tolerates fractional seconds.
    """
    return int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())


def _record_to_row(record: dict, username: str) -> dict:
    return {
        "username": username,
        "played_at": _to_epoch(record["ts"]),
        "ms_played": record.get("ms_played") or 0,
        "track_name": record.get("master_metadata_track_name"),
        "artist_name": record.get("master_metadata_album_artist_name"),
        "album_name": record.get("master_metadata_album_album_name"),
        "track_uri": record.get("spotify_track_uri"),
        "platform": record.get("platform"),
        "conn_country": record.get("conn_country"),
        "reason_start": record.get("reason_start"),
        "reason_end": record.get("reason_end"),
        "shuffle": bool(record.get("shuffle")),
        "skipped": bool(record.get("skipped")),
        "episode_name": record.get("episode_name"),
        "episode_show_name": record.get("episode_show_name"),
    }


def import_archive(
    db: Session,
    archive_dir: str | Path,
    username: str,
    *,
    pattern: str = "Streaming_History_Audio_*.json",
    replace: bool = True,
) -> int:
    """Load every matching JSON file under ``archive_dir`` for ``username``.

    Returns the number of listens imported.
    """
    archive_dir = Path(archive_dir)
    if not archive_dir.is_dir():
        raise FileNotFoundError(f"Archive directory not found: {archive_dir}")

    files = sorted(archive_dir.glob(pattern))  # sorted -> chronological-ish load
    if not files:
        raise FileNotFoundError(f"No files matching {pattern!r} in {archive_dir}")

    rows: list[dict] = []
    for file_path in files:
        with open(file_path, encoding="utf-8") as f:
            rows.extend(_record_to_row(rec, username) for rec in json.load(f))

    if replace:
        db.execute(delete(Listen).where(Listen.username == username))
    if rows:
        db.execute(insert(Listen), rows)  # single bulk insert (executemany)
    db.commit()
    return len(rows)
