from fastapi import FastAPI, Header, Query, Path, Body, Form, File, UploadFile, HTTPException, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, AfterValidator, Field, EmailStr
from typing import Annotated, Any
from enum import Enum
from random import random

app = FastAPI()

# localhost:8000/docs#
# localhost:8000/redoc
# localhost:8000/openapi.json

@app.get("/hi")
async def read_user_me():
    return {"Hello": "World!"}
