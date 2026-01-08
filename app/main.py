from fastapi import FastAPI, Header, Query, Path, Body, Form, File, UploadFile, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, AfterValidator, Field, EmailStr
from typing import Annotated, Any
from enum import Enum
from random import random

from app.utils.stats_manager import StatsManager
from app.database import get_db

app = FastAPI()

# localhost:8000/docs#
# localhost:8000/redoc
# localhost:8000/openapi.json

# make a field public/privat stats, and maybe do not tie them to User object? think about

@app.get("/hi")
async def read_user_me():
    return {"Hello": "World!"}

@app.get("/stats/{username}")
async def calculate_stats(username: str, db: Session = Depends(get_db)):
    try:
        if StatsManager.stats_exist_for_user(username, db):
            stats = StatsManager.get_stats_for_user(username, db)
            return stats
        else:
            stats = StatsManager.calculate_stats_for_user(username, db)
            return {
                'message': f'Stats calculated successfully for {username}',
                'data': stats
            }
    except Exception as e:
        return {'error': f'Error calculating stats: {str(e)}'}, 500

@app.get("/stats/{username}/status")
async def stats_status(username: str, db: Session = Depends(get_db)):
    try:
        return StatsManager.stats_exist_for_user(username, db)
    except Exception as e:
        return {'error': f'Error calculating stats: {str(e)}'}, 500

@app.get('/stats/{username}/{stat}')
def get_total_listening_time(username: str, stat: str, db: Session = Depends(get_db)):
    ''' Display the total listening time in ms/min/hour/day '''
    stats = StatsManager.get_stats_for_user(username, db)
    if not stats:
        return {'error': 'Stats not found. Please calculate stats first.'}, 404
    print(stats)
    return stats[stat]
