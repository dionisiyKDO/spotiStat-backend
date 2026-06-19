"""Dashboard stats endpoints (the single-page bundle)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from spotistat.db.session import get_db
from spotistat.services import stats as stats_service

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/{username}/dashboard")
def get_dashboard(username: str, db: Session = Depends(get_db)) -> dict:
    """Everything the single-page dashboard needs, in one precomputed bundle."""
    bundle = stats_service.load_dashboard(db, username)
    if bundle is None:
        raise HTTPException(
            status_code=404,
            detail=f"No stats for {username!r}. Import the archive and recompute first.",
        )
    return bundle
