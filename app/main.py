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

@app.get("/calculate_stats")
async def calculate_stats(db: Session = Depends(get_db)):
    result = StatsManager.calculate_stats_for_user('dionisiy', db)
    return result
