# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from app.config import Config

# The actual connection
engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI, 
    connect_args={"check_same_thread": False} # Needed only for SQLite
)

# Creates new sessions for each request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# The Base Class. All database models will inherit from this
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()