from flask import Blueprint

spotify_bp = Blueprint('spotify', __name__, prefix='/spotify')

from . import routes