from flask import Blueprint, jsonify, render_template, request, session, redirect, url_for, send_file, current_app

from . import main_bp

from app.blueprints.auth.routes import get_spotify_client
from app.utils.utils import *

import pandas as pd
from werkzeug.utils import secure_filename
import os

# @main_bp.route('/', methods=['GET', 'POST'])
# def index():
#     if 'token_info' not in session:
#         return render_template('index.html')
#     return render_template('index.html')

@main_bp.route('/user_info')
def user_info():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    sp = get_spotify_client()
    user_info = sp.current_user()
    
    return jsonify(user_info=user_info)

@main_bp.route('/import_history')
def import_history():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    tmp = read_json_and_store_data(json_directory='./app/data/dionisiy')

    return jsonify(tmp.to_dict())


@main_bp.route('/get_record/<id>')
def get_record(id):
    # TODO: check if id is valid, there is an entry with that id
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    tmp = db_session.query(StreamingHistory).get(id)
    
    return jsonify(tmp.to_dict())

@main_bp.route('/process')
def process_data():
    # Retrieve stored dataframes
    dataframes = current_app.config.get('DATAFRAMES', [])

    # Render a template or perform processing
    # For now, we will just return a success message
    return "Data uploaded successfully. You can now process it."

@main_bp.route('/search_saved_tracks', methods=['GET'])
def search_saved_tracks():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    sp = get_spotify_client()
    year = request.args.get("year")
    
    results = select_saved_tracks(sp, year)
    
    return jsonify(results=results)

@main_bp.route('/results')
def results():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    sp = get_spotify_client()
    top_tracks = get_top_tracks(sp)
    return jsonify(top_tracks=top_tracks)

@main_bp.route('/play_history')
def play_history():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    sp = get_spotify_client()
    play_history = get_play_history(sp)
    return jsonify(play_history=play_history)

@main_bp.route('/liked_tracks')
def full_liked_tracks():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    limit = request.args.get('limit', None, type=int)
    offset = request.args.get('offset', None, type=int)
    
    sp = get_spotify_client()
    liked_tracks = get_liked_tracks(sp, limit, offset)
    
    # Add index to each track
    for index, track in enumerate(liked_tracks):
        track['index'] = index

    # Get sorting parameters from the query string
    sort_by = request.args.get('sort_by', 'index')
    reverse = request.args.get('order', 'asc') == 'desc'
    
    # Sort the tracks based on the query parameter
    if sort_by in {'index', 'name', 'artist', 'popularity'}:
        liked_tracks.sort(key=lambda x: x.get(sort_by), reverse=reverse)
    
    # Return the liked tracks as JSON
    return jsonify(liked_tracks=liked_tracks)

# Section for top artists and top tracks
# region
@main_bp.route('/top_artists', methods=['GET'])
def top_artists():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    time_range = request.args.get('time_range', 'medium_term')
    sp = get_spotify_client()
    top_artists = get_top_artists(sp, time_range)
    
    return jsonify(top_artists=top_artists)

@main_bp.route('/top_tracks', methods=['GET'])
def top_tracks():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    time_range = request.args.get('time_range', 'medium_term')
    sp = get_spotify_client()
    top_tracks = get_top_tracks(sp, time_range)
    
    return jsonify(top_tracks=top_tracks)
# endregion

@main_bp.route('/tracks_by_year', methods=['GET'])
def tracks_by_year():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    sp = get_spotify_client()
    tracks_by_year = get_tracks_by_year(sp)
    
    return jsonify(tracks_by_year=tracks_by_year)
