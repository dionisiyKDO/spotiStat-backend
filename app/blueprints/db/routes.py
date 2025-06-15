from flask import jsonify, request
from sqlalchemy import func, extract
from datetime import datetime

# from app.blueprints.auth.routes import get_spotify_client
from app.models import StreamingHistory
from app.database import db_session
from . import db_bp

MS_IN_HOUR = 1000 * 60 * 60
