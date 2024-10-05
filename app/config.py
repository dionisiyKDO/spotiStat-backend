from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
    SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
    SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app/data/streaming_history.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_DEFAULT_TIMEOUT = 1200  # 20 minutes
    str_datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
