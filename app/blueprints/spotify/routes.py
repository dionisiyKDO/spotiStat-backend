from flask import jsonify, request, session
from functools import wraps
import os

from app.blueprints.auth.routes import get_spotify_client
from app.utils.utils import *
from .utils import *

from . import spotify_bp

# token_required decorator
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'token_info' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Endpoint for getting current user info, mainly for profile info and avatar
@spotify_bp.route('/spotify/profile', methods=['GET'])
@token_required
def get_spotify_profile():    
    sp = get_spotify_client()
    user_info = sp.current_user()

    return jsonify(user_info=user_info)
