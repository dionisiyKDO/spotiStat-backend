from flask import Blueprint

spotify_bp = Blueprint('spotify', __name__, url_prefix='/spotify')

from . import routes