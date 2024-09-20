from flask import jsonify, request, session
import os

from app.blueprints.auth.routes import get_spotify_client
from app.utils.utils import *
from . import main_bp


# SP API: Endpoint for getting current user info, mainly for profile info and avatar
@main_bp.route('/user_info')
def user_info():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    sp = get_spotify_client()
    user_info = sp.current_user()
    
    return jsonify(user_info=user_info)

# SP API: Get saved tracks by filter, rn only filter by year, can add more filters later
@main_bp.route('/search_saved_tracks', methods=['GET'])
def search_saved_tracks():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    sp = get_spotify_client()
    year = request.args.get("year")
    
    results = select_saved_tracks(sp, year)
    
    return jsonify(results=results)

# SP API: Get last {limit} played tracks
@main_bp.route('/play_history')
def play_history():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    limit = request.args.get('limit', None, type=int)
    
    sp = get_spotify_client()
    play_history = get_play_history(sp, limit)
    
    return jsonify(play_history=play_history)

# SP API: Get {limit} liked tracks, if limit is None, get all liked tracks
@main_bp.route('/liked_tracks')
def full_liked_tracks():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    limit = request.args.get('limit', None, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    sp = get_spotify_client()
    liked_tracks = get_liked_tracks(sp, limit, offset)
    
    # Add index to each track
    for index, track in enumerate(liked_tracks):
        track['index'] = index

    # Get sorting parameters from the query string
    sort_by = request.args.get('sort_by', 'index') # Get sort_by parameter from the query string, default to 'index'
    reverse = request.args.get('order', 'asc') == 'desc' # True if order is descending, False otherwise
    
    # Sort the tracks based on the query parameter
    if sort_by in {'index', 'name', 'artist', 'popularity'}:
        liked_tracks.sort(key=lambda x: x.get(sort_by), reverse=reverse)
    
    return jsonify(liked_tracks=liked_tracks)

# SP API: Get top artists
@main_bp.route('/top_artists', methods=['GET'])
def top_artists():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    time_range = request.args.get('time_range', 'medium_term')
    
    sp = get_spotify_client()
    top_artists = get_top_artists(sp, time_range)
    
    return jsonify(top_artists=top_artists)

# SP API: Get top tracks
@main_bp.route('/top_tracks', methods=['GET'])
def top_tracks():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    time_range = request.args.get('time_range', 'medium_term')
    
    sp = get_spotify_client()
    top_tracks = get_top_tracks(sp, time_range)
    
    return jsonify(top_tracks=top_tracks)

# SP API: Get tracks count by each year
@main_bp.route('/tracks_by_year', methods=['GET'])
def tracks_by_year():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    sp = get_spotify_client()
    tracks_by_year = get_tracks_by_year(sp)
    
    return jsonify(tracks_by_year=tracks_by_year)
