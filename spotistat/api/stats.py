"""User stats endpoints — the precomputed dashboard bundle plus live drill-downs.

All read endpoints live under ``/stats/{username}`` and accept an optional period:
``?period=all`` (default), ``?period=3m`` / ``12m`` (rolling), ``?period=2023`` (a
year), or explicit ``?start=YYYY-MM-DD&end=YYYY-MM-DD``. ``all`` is served from the
precomputed bundle; any narrower period is computed live.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from spotistat.db.session import get_db
from spotistat.period import resolve_period
from spotistat.services import library as library_service
from spotistat.services import stats as stats_service

router = APIRouter(prefix="/stats", tags=["stats"])

Bounds = tuple[int | None, int | None]


def period_range(
    period: str = "all", start: str | None = None, end: str | None = None
) -> Bounds:
    """Shared query params -> (start, end) epoch bounds; 400 on a bad selector."""
    try:
        return resolve_period(period, start, end)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{username}/dashboard")
def get_dashboard(
    username: str, bounds: Bounds = Depends(period_range), db: Session = Depends(get_db)
) -> dict:
    """The single-page dashboard bundle. All-time is precomputed; periods compute live."""
    start, end = bounds
    if start is None and end is None:
        bundle = stats_service.load_dashboard(db, username)
        if bundle is None:
            raise HTTPException(
                status_code=404,
                detail=f"No stats for {username!r}. Import the archive and recompute first.",
            )
        return bundle
    return stats_service.dashboard_for_period(db, username, start, end)


@router.get("/{username}/artists")
def list_artists(
    username: str, bounds: Bounds = Depends(period_range),
    limit: int | None = None, db: Session = Depends(get_db),
) -> list[dict]:
    """Artists with over 10 minutes of listening in the period, most-played first."""
    start, end = bounds
    return library_service.list_artists(db, username, start=start, end=end, limit=limit)


@router.get("/{username}/artists/{artist_name}")
def artist_detail(
    username: str, artist_name: str, bounds: Bounds = Depends(period_range),
    db: Session = Depends(get_db),
) -> dict:
    """Totals and a per-day timeline for one artist."""
    start, end = bounds
    detail = library_service.artist_detail(db, username, artist_name, start=start, end=end)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"No plays for artist {artist_name!r}.")
    return detail


@router.get("/{username}/artists/{artist_name}/tracks")
def artist_tracks(
    username: str, artist_name: str, bounds: Bounds = Depends(period_range),
    db: Session = Depends(get_db),
) -> list[dict]:
    """An artist's tracks, most-played first."""
    start, end = bounds
    return library_service.artist_tracks(db, username, artist_name, start=start, end=end)


@router.get("/{username}/tracks")
def list_tracks(
    username: str, bounds: Bounds = Depends(period_range),
    limit: int | None = None, db: Session = Depends(get_db),
) -> list[dict]:
    """Tracks with over 10 minutes of listening in the period, most-played first."""
    start, end = bounds
    return library_service.list_tracks(db, username, start=start, end=end, limit=limit)


@router.get("/{username}/tracks/{track_id}")
def track_detail(
    username: str, track_id: str, bounds: Bounds = Depends(period_range),
    db: Session = Depends(get_db),
) -> dict:
    """Totals, per-day timeline, and estimated song length for one track."""
    start, end = bounds
    detail = library_service.track_detail(db, username, track_id, start=start, end=end)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"No plays for track {track_id!r}.")
    return detail
