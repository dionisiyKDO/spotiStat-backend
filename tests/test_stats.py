from datetime import datetime

import pytest
from sqlalchemy import create_engine, insert
from sqlalchemy.orm import Session

from spotistat.db.models import Base, Listen
from spotistat.services import stats as stats_service


def _epoch(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _seed(db) -> None:
    rows = [
        # two plays 2 min apart -> one session of 305000 ms
        {"username": "u", "played_at": _epoch("2021-01-01T10:00:00Z"), "ms_played": 300000,
         "artist_name": "A", "track_name": "s1", "track_uri": "uri1",
         "reason_end": "trackdone", "skipped": False, "platform": "Windows 10"},
        {"username": "u", "played_at": _epoch("2021-01-01T10:02:00Z"), "ms_played": 5000,
         "artist_name": "A", "track_name": "s2", "track_uri": "uri2",
         "reason_end": "fwdbtn", "skipped": True, "platform": "Windows 10"},
        # next day -> separate session of 200000 ms
        {"username": "u", "played_at": _epoch("2021-01-02T23:00:00Z"), "ms_played": 200000,
         "artist_name": "B", "track_name": "s3", "track_uri": "uri3",
         "reason_end": "trackdone", "skipped": False, "platform": "Android"},
    ]
    db.execute(insert(Listen), rows)
    db.commit()


def test_recompute_and_load(db):
    _seed(db)
    stats_service.recompute(db, "u")

    bundle = stats_service.load_dashboard(db, "u")
    assert bundle is not None
    stats = bundle["stats"]

    assert stats["total_listening_time"]["total_listening_ms"] == 505000
    assert stats["skip_stats"]["skipped_tracks"] == 1
    assert stats["unique_tracks_count"]["unique_tracks_count"] == 3
    assert stats["top_artists"][0]["artist"] == "A"  # 305000 ms beats B's 200000

    longest = stats["longest_session"]
    assert longest["total_tracks"] == 2
    assert longest["total_ms_played"] == 305000

    platforms = {p["platform"]: p for p in stats["platform_stats"]}
    assert platforms["Windows"]["play_count"] == 2
    assert platforms["Android"]["play_count"] == 1

    assert len(stats["listening_by_hour"]) == 24  # zero-filled


def test_load_dashboard_none_when_empty(db):
    assert stats_service.load_dashboard(db, "nobody") is None


def test_calculate_all_respects_period_bounds(db):
    from zoneinfo import ZoneInfo

    db.execute(insert(Listen), [
        {"username": "u", "played_at": _epoch("2021-05-01T10:00:00Z"), "ms_played": 100000,
         "artist_name": "Old", "track_name": "o", "track_uri": "uo",
         "reason_end": "trackdone", "skipped": False, "platform": "Windows"},
        {"username": "u", "played_at": _epoch("2023-05-01T10:00:00Z"), "ms_played": 200000,
         "artist_name": "New", "track_name": "n", "track_uri": "un",
         "reason_end": "trackdone", "skipped": False, "platform": "Windows"},
    ])
    db.commit()

    start = _epoch("2023-01-01T00:00:00Z")
    end = _epoch("2024-01-01T00:00:00Z")
    result = stats_service.calculate_all(db, "u", ZoneInfo("Europe/Kyiv"), start=start, end=end)

    assert result["total_listening_time"]["total_listening_ms"] == 200000  # only the 2023 play
    assert [a["artist"] for a in result["top_artists"]] == ["New"]
