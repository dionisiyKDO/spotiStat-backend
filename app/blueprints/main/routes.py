from flask import jsonify, request, session
from functools import wraps
import os

from app.blueprints.auth.routes import get_spotify_client
from app.utils.utils import *
from .utils import *
from . import main_bp


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'token_info' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# TODO: think about handling multiple users
# SP API: Endpoint for getting current user info, mainly for profile info and avatar
@main_bp.route('/spotify/profile', methods=['GET'])
@token_required
def get_spotify_profile():
    sp = get_spotify_client()
    user_info = sp.current_user()
    # user_info = sp.user(id='fqn9lnigp2iqiecxw2wyroyml')

    return jsonify(user_info=user_info)

@main_bp.route('/spotify/track_meta', methods=['GET'])
@token_required
def get_track_meta():
    track_id = request.args.get('track_id', default='4DMKwE2E2iYDKY01C335Uw', type=str)
    
    sp = get_spotify_client()
    track_meta = sp.track(track_id=track_id)

    return jsonify(track_meta=track_meta)

# SP API: Get saved tracks by filter, rn only filter by year, can support more filters
@main_bp.route('/spotify/saved_tracks/filter', methods=['GET'])
@token_required
def filter_saved_tracks():
    sp = get_spotify_client()
    year = request.args.get("year")
    
    # Later on, more filters can be added (e.g., genre, artist, etc.)
    results = select_saved_tracks(sp, year)
    
    return jsonify(results=results)

# SP API: Get last {limit} played tracks
@main_bp.route('/spotify/recently_played', methods=['GET'])
@token_required
def get_recently_played_tracks():
    limit = request.args.get('limit', None, type=int)
    
    sp = get_spotify_client()
    play_history = get_play_history(sp, limit)
    
    return jsonify(play_history=play_history)

# SP API: Get {limit} liked tracks, if limit is None, get all liked tracks
@main_bp.route('/spotify/saved_tracks', methods=['GET'])
@token_required
def get_saved_tracks():
    limit = request.args.get('limit', None, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    sp = get_spotify_client()
    saved_tracks = get_liked_tracks(sp, limit, offset)
    
    # Add index to each track
    for index, track in enumerate(saved_tracks):
        track['index'] = index + offset

    # Get sorting parameters from the query string
    sort_by = request.args.get('sort_by', 'index') # Get sort_by parameter from the query string, default to 'index'
    reverse = request.args.get('order', 'asc') == 'desc' # True if order is descending, False otherwise
    
    # Supported sorting fields: index, name, artist, popularity
    if sort_by in {'index', 'name', 'artist', 'popularity'}:
        saved_tracks.sort(key=lambda x: x.get(sort_by), reverse=reverse)
    
    return jsonify(saved_tracks=saved_tracks)

# SP API: Get top artists
@main_bp.route('/spotify/top_artists', methods=['GET'])
@token_required
def get_top_spotify_artists():
    time_range = request.args.get('time_range', 'medium_term')
    
    sp = get_spotify_client()
    top_artists = get_top_artists(sp, time_range)
    
    return jsonify(top_artists=top_artists)

# SP API: Get top tracks
@main_bp.route('/spotify/top_tracks', methods=['GET'])
@token_required
def get_top_spotify_tracks():
    time_range = request.args.get('time_range', 'medium_term')
    
    sp = get_spotify_client()
    top_tracks = get_top_tracks(sp, time_range)
    
    return jsonify(top_tracks=top_tracks)

# SP API: Get tracks count by each year
@main_bp.route('/spotify/tracks_by_year', methods=['GET'])
@token_required
def get_spotify_tracks_by_year():
    sp = get_spotify_client()
    tracks_by_year = get_tracks_by_year(sp)
    
    return jsonify(tracks_by_year=tracks_by_year)
