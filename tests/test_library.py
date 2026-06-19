from datetime import datetime

import pytest
from sqlalchemy import create_engine, insert
from sqlalchemy.orm import Session

from spotistat.db.models import Base, Listen
from spotistat.services import library


def _epoch(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _play(ts, ms, artist, track, uri, reason="trackdone"):
    return {
        "username": "u", "played_at": _epoch(ts), "ms_played": ms,
        "artist_name": artist, "track_name": track, "track_uri": uri,
        "reason_end": reason, "skipped": False, "platform": "Windows",
    }


def _seed(db) -> None:
    rows = [
        # A / s1: three natural finishes of 240000 -> 720000 ms, song_length 240000
        _play("2021-01-01T10:00:00Z", 240000, "A", "s1", "spotify:track:t1"),
        _play("2021-01-01T11:00:00Z", 240000, "A", "s1", "spotify:track:t1"),
        _play("2021-01-02T10:00:00Z", 240000, "A", "s1", "spotify:track:t1"),
        # A / s2: one short skip, no trackdone -> below threshold, song_length None
        _play("2021-01-02T11:00:00Z", 5000, "A", "s2", "spotify:track:t2", "fwdbtn"),
        # B / s3: four plays of 200000 -> 800000 ms
        _play("2021-01-03T10:00:00Z", 200000, "B", "s3", "spotify:track:t3"),
        _play("2021-01-03T11:00:00Z", 200000, "B", "s3", "spotify:track:t3"),
        _play("2021-01-03T12:00:00Z", 200000, "B", "s3", "spotify:track:t3"),
        _play("2021-01-03T13:00:00Z", 200000, "B", "s3", "spotify:track:t3"),
        # C / s4: single 100000 play -> below the 10-minute threshold
        _play("2021-01-05T10:00:00Z", 100000, "C", "s4", "spotify:track:t4"),
        # podcast: null track/artist, large ms -> must be excluded from track list
        {"username": "u", "played_at": _epoch("2021-01-04T10:00:00Z"), "ms_played": 900000,
         "artist_name": None, "track_name": None, "track_uri": None,
         "reason_end": "endplay", "skipped": False, "platform": "Windows"},
    ]
    db.execute(insert(Listen), rows)
    db.commit()


def test_list_artists_orders_by_time_and_applies_threshold(db):
    _seed(db)
    names = [a["artist"] for a in library.list_artists(db, "u")]
    assert names == ["B", "A"]  # B 800000 > A 725000; C (100000) below threshold, excluded


def test_list_tracks_excludes_podcasts_and_below_threshold(db):
    _seed(db)
    names = [t["track_name"] for t in library.list_tracks(db, "u")]
    assert names == ["s3", "s1"]  # s2/s4 below threshold; null-name podcast excluded


def test_track_detail_estimates_song_length_from_trackdone(db):
    _seed(db)
    detail = library.track_detail(db, "u", "t1")
    assert detail["total_plays"] == 3
    assert detail["total_ms_played"] == 720000
    assert detail["song_length"] == 240000
    assert detail["distinct_days_played"] == 2


def test_track_detail_song_length_none_without_trackdone(db):
    _seed(db)
    detail = library.track_detail(db, "u", "t2")  # only a fwdbtn play
    assert detail["song_length"] is None  # the bug fix: None, not a crash


def test_artist_detail_totals_and_missing(db):
    _seed(db)
    detail = library.artist_detail(db, "u", "A")
    assert detail["total_plays"] == 4
    assert detail["total_ms_played"] == 725000
    assert library.artist_detail(db, "u", "ghost") is None


def test_artist_tracks_ordered_by_time(db):
    _seed(db)
    assert [t["track_name"] for t in library.artist_tracks(db, "u", "A")] == ["s1", "s2"]


def test_list_artists_respects_period(db):
    _seed(db)
    start = _epoch("2021-01-03T00:00:00Z")
    end = _epoch("2021-01-04T00:00:00Z")
    names = [a["artist"] for a in library.list_artists(db, "u", start=start, end=end)]
    assert names == ["B"]  # only B played within 2021-01-03
