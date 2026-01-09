from fastapi import FastAPI, Header, Query, Path, Body, Form, File, UploadFile, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, AfterValidator, Field, EmailStr
from typing import Annotated, Any
from enum import Enum
from random import random

from app.database import get_db
from app.services.stats import StatsService

app = FastAPI()

# localhost:8000/docs#
# localhost:8000/redoc
# localhost:8000/openapi.json

# make a field public/privat stats, and maybe do not tie them to User object? think about
# insert Pydantic schemas

@app.get("/stats/{username}")
async def calculate_stats(username: str, db: Session = Depends(get_db)):
    """
    Get all general stats for user
    
    :param username: Users username
    :type username: str
    :param db: Database session injection
    :type db: Session
    """
    try:
        stats = StatsService.get_stats_for_user(username, False, db)
        return stats
    except Exception as e:
        return {'error': f'Error calculating stats: {str(e)}'}, 500

@app.get("/stats/{username}/status")
async def stats_status(username: str, db: Session = Depends(get_db)):
    """
    Get status if stats exist for user
    
    :param username: Users username
    :type username: str
    :param db: Database session injection
    :type db: Session
    """
    try:
        return StatsService.stats_exist_for_user(username, db)
    except Exception as e:
        return {'error': f'Error calculating stats: {str(e)}'}, 500

@app.get("/stats/{username}/listened-tracks")
async def get_most_tracks(username: str, db: Session = Depends(get_db)):
    """
    Get all listened tracks for user ordered by hours listened
    
    :param username: Users username
    :type username: str
    :param db: Database session injection
    :type db: Session
    """
    service = StatsService(db)
    stats = service.get_most_tracks(username)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Stats not found")
    
    return stats

@app.get("/stats/{username}/listened-artists")
async def get_most_artists(username: str, db: Session = Depends(get_db)):
    """
    Get all listened artists for user ordered by hours listened
    
    :param username: Users username
    :type username: str
    :param db: Database session injection
    :type db: Session
    """
    service = StatsService(db)
    stats = service.get_most_artists(username)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Stats not found")
    
    return stats

@app.get("/stats/{username}/track/{track_id}")
async def get_track_stats(username: str, track_id: str, db: Session = Depends(get_db)):
    """
    Get detailed stats for a specific track
    
    :param username: Users username
    :type username: str
    :param track_id: Spotify Track ID
    :type track_id: str
    :param db: Database session injection
    :type db: Session
    """
    service = StatsService(db)
    stats = service.get_track_details(username, track_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Track not found")
    
    return stats

@app.get("/stats/{username}/artist/{artist_name}")
async def get_artist_stats(username: str, artist_name: str, db: Session = Depends(get_db)):
    """
    Get detailed stats for a specific artist
    
    :param username: Users username
    :type username: str
    :param artist_name: Name of the artist
    :type artist_name: str
    :param db: Database session injection
    :type db: Session
    """
    service = StatsService(db)
    stats = service.get_artist_stats(username, artist_name)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Stats not found")
    
    return stats

@app.get("/stats/{username}/artist/{artist_name}/listened-tracks")
async def get_artists_tracks(username: str, artist_name: str, db: Session = Depends(get_db)):
    """
    Get all listened tracks for a specific artist

    :param username: Users username
    :type username: str
    :param artist_name: Name of the artist
    :type artist_name: str
    :param db: Database session injection
    :type db: Session
    """
    service = StatsService(db)
    stats = service.get_artists_tracks(username, artist_name)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Stats not found")
    
    return stats


# @app.post("/upload-history/")
# async def upload_history(
#     username: str, 
#     file: UploadFile = File(...), 
#     db: Session = Depends(get_db)
# ):
#     # Save temp file
#     temp_path = f"temp_{file.filename}"
#     with open(temp_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
        
#     # Run the service
#     result = services.bulk_import_history(db, temp_path, username)
    
#     # Clean up
#     os.remove(temp_path)
    
#     if result:
#         return {"status": "success", "filename": file.filename}
#     return {"status": "failed"}

# class StatName(str, Enum):
#     username = "username"
#     calculated_at = "calculated_at"
#     total_listening_time = "total_listening_time"
#     platform_stats = "platform_stats"
#     most_skipped_tracks = "most_skipped_tracks"
#     skip_stats = "skip_stats"
#     end_reasons = "end_reasons"
#     unique_tracks_count = "unique_tracks_count"
#     top_artists = "top_artists"
#     top_tracks = "top_tracks"
#     listening_by_hour = "listening_by_hour"
#     listening_by_year = "listening_by_year"
#     listening_by_month = "listening_by_month"
#     listening_by_weekday = "listening_by_weekday"
#     listening_by_date = "listening_by_date"
#     longest_session = "longest_session"
    
# @app.get('/stats/{username}/{stat}')
# def get_total_listening_time(username: str, stat: StatName, db: Session = Depends(get_db)):
#     ''' Display the total listening time in ms/min/hour/day '''
#     stats = StatsService.get_stats_for_user(username, False, db)
#     if not stats:
#         return {'error': 'Stats not found. Please calculate stats first.'}, 404
#     print(stats)
#     return stats[stat]