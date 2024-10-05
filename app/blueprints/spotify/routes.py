from flask import jsonify, request, session
from functools import wraps
from app.blueprints.auth.routes import get_spotify_client
from app.utils.spotify_utils import *

from . import spotify_bp

# Decorator for checking if the token is present in the session
def token_required(f):
    '''A decorator that checks if the user is authenticated via a valid token. 
    If not, it returns a 401 error.'''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'token_info' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function



# Route: Fetch Spotify user profile
@spotify_bp.route('/profile', methods=['GET'])
@token_required
def get_spotify_profile():
    ''' Returns the current Spotify user profile information (avatar, display name, etc.). '''
    sp = get_spotify_client()
    user_info = sp.current_user()
    return jsonify(user_info=user_info)

# Route: Get metadata for a specific track
@spotify_bp.route('/track_meta', methods=['GET'])
@token_required
def fetch_track_meta():
    '''Fetch metadata for a specific Spotify track by its track ID.
    Example: /spotify/track_meta?track_id=<track_id>'''
    track_id = request.args.get('track_id', default='4DMKwE2E2iYDKY01C335Uw', type=str)
    sp = get_spotify_client()
    track_meta = sp.track(track_id)
    return jsonify(track_meta=track_meta)

# Route: Fetch saved/liked tracks
@spotify_bp.route('/saved_tracks', methods=['GET'])
@token_required
def fetch_saved_tracks():
    '''Fetches liked/saved tracks of the user. Supports pagination and sorting.
    Example: /saved_tracks?limit=20&offset=0&sort_by=name&order=desc'''
    limit = request.args.get('limit', None, type=int)
    offset = request.args.get('offset', 0, type=int)
    sort_by = request.args.get('sort_by', 'index')
    reverse = request.args.get('order', 'asc') == 'desc' # True if order is descending, False otherwise
    
    sp = get_spotify_client()
    saved_tracks = get_liked_tracks(sp, limit, offset)
    
    # Add index to each track
    for index, track in enumerate(saved_tracks):
        track['index'] = index + offset
    
    # Sort tracks based on supported fields
    if sort_by in {'index', 'name', 'artist', 'popularity'}:
        saved_tracks.sort(key=lambda x: x.get(sort_by), reverse=reverse)
    
    return jsonify(saved_tracks=saved_tracks)

# Route: Filter saved tracks (currently by year, can support more)
@spotify_bp.route('/saved_tracks/filter', methods=['GET'])
@token_required
def fetch_filtered_saved_tracks():
    '''Fetch saved tracks filtered by certain criteria (currently only supports filtering by year).
    Example: /saved_tracks/filter?year=2020'''
    year = request.args.get("year")
    sp = get_spotify_client()
    results = select_saved_tracks(sp, year)
    return jsonify(results=results)

# Route: Fetch recently played tracks
@spotify_bp.route('/recently_played', methods=['GET'])
@token_required
def fetch_recently_played_tracks():
    '''Fetch the user's recently played tracks, with an optional limit.
    Example: /recently_played?limit=10'''
    limit = request.args.get('limit', None, type=int)
    sp = get_spotify_client()
    play_history = get_play_history(sp, limit)
    return jsonify(play_history=play_history)

# Route: Fetch top Spotify artists for the user
@spotify_bp.route('/top_artists', methods=['GET'])
@token_required
def fetch_top_spotify_artists():
    '''Fetch the user's top artists. Optionally specify time range ('short_term', 'medium_term', 'long_term').
    Example: /top_artists?time_range=long_term'''
    time_range = request.args.get('time_range', 'medium_term')
    sp = get_spotify_client()
    top_artists = get_top_artists(sp, time_range)
    return jsonify(top_artists=top_artists)

# Route: Fetch top Spotify tracks for the user
@spotify_bp.route('/top_tracks', methods=['GET'])
@token_required
def fetch_top_spotify_tracks():
    '''Fetch the user's top tracks. Optionally specify time range ('short_term', 'medium_term', 'long_term').
    Example: /top_tracks?time_range=long_term'''
    time_range = request.args.get('time_range', 'medium_term')
    sp = get_spotify_client()
    top_tracks = get_top_tracks(sp, time_range)
    return jsonify(top_tracks=top_tracks)

# Route: Fetch tracks by year
@spotify_bp.route('/tracks_by_year', methods=['GET'])
@token_required
def fetch_tracks_by_year():
    '''Get the user's saved tracks categorized by the year of release.'''
    sp = get_spotify_client()
    tracks_by_year = get_tracks_by_year(sp)
    return jsonify(tracks_by_year=tracks_by_year)
