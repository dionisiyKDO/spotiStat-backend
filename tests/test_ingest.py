import json

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from spotistat.db.models import Base, Listen
from spotistat.services.ingest import import_archive


@pytest.fixture
def db(tmp_path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _write_archive(folder, records) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "Streaming_History_Audio_2021.json").write_text(
        json.dumps(records), encoding="utf-8"
    )


def test_import_archive_loads_rows_and_parses_time(db, tmp_path):
    archive = tmp_path / "tester"
    _write_archive(
        archive,
        [
            {
                "ts": "2021-01-01T10:00:00Z",
                "ms_played": 60000,
                "master_metadata_track_name": "Song A",
                "master_metadata_album_artist_name": "Artist X",
                "spotify_track_uri": "spotify:track:abc",
                "skipped": False,
            },
            {
                "ts": "2021-01-01T10:05:00Z",
                "ms_played": 1000,
                "master_metadata_track_name": "Song B",
                "master_metadata_album_artist_name": "Artist Y",
                "skipped": True,
            },
        ],
    )

    count = import_archive(db, archive, "tester")

    assert count == 2
    assert db.scalar(select(func.count()).select_from(Listen)) == 2
    first = db.scalars(select(Listen).order_by(Listen.played_at)).first()
    assert first.artist_name == "Artist X"
    assert first.played_at == 1609495200  # 2021-01-01T10:00:00Z in epoch seconds
    assert first.skipped is False


def test_import_is_idempotent_per_user(db, tmp_path):
    archive = tmp_path / "tester"
    _write_archive(
        archive,
        [{"ts": "2021-01-01T10:00:00Z", "ms_played": 1000}],
    )

    import_archive(db, archive, "tester")
    import_archive(db, archive, "tester")  # re-import should replace, not duplicate

    assert db.scalar(select(func.count()).select_from(Listen)) == 1


def test_missing_archive_raises(db, tmp_path):
    with pytest.raises(FileNotFoundError):
        import_archive(db, tmp_path / "does_not_exist", "nobody")
