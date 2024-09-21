from flask import jsonify, session, current_app, request
from sqlalchemy import func, desc
import pandas as pd

from app.blueprints.auth.routes import get_spotify_client
from app.utils.utils import *
from . import db_bp

MS_IN_HOUR = 1000 * 60 * 60

# NOW it is route for importing json files from pc, and storing them in sqllite db
# Ideally, it should be a route to accept json files from the frontend, and store them in the db
@db_bp.route('/upload_history')
# @db_bp.route('/upload_history', methods=['POST'])
def upload_history():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    # if not request.is_json:
    #     return jsonify({'error': 'Invalid input, expected JSON'}), 400
    # data = request.get_json()
    # try:
    #     tmp = read_json_and_store_data(json_data=data)
    # except Exception as e:
    #     return jsonify({'error': f'Failed to process data: {str(e)}'}), 500
    
    tmp = read_json_and_store_data(json_directory='./app/data/dionisiy')

    return jsonify(tmp.to_dict())

# Get specific record from listening history
@db_bp.route('/history/record/<int:id>', methods=['GET'])
def get_streaming_record(id):
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    record = db_session.query(StreamingHistory).get(id)
    if not record:
        return jsonify({'error': f'Record with id {id} not found'}), 404
    
    return jsonify(record.to_dict())

# Route for getting top played tracks by time played
@db_bp.route('/history/top_tracks_by_playtime', methods=['GET'])
def get_top_played_tracks():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    sp = get_spotify_client()

    limit = request.args.get('limit', default=10, type=int)  # Read limit from query params

    query = ( # query for track name, artist and total ms played, grouped by track name to sum up total ms played, and order by total ms played descending
        db_session.query(
            StreamingHistory.master_metadata_track_name,
            StreamingHistory.master_metadata_album_artist_name,
            StreamingHistory.spotify_track_uri,
            func.sum(StreamingHistory.ms_played).label('total_ms_played')
        )
        .filter(StreamingHistory.master_metadata_track_name.isnot(None))
        .group_by(StreamingHistory.master_metadata_track_name, StreamingHistory.master_metadata_album_artist_name)
        .order_by(desc('total_ms_played'))
        .limit(limit) # how many top tracks to return
    )
    
    enumerated_query = enumerate(query)
    
    # Convert the result into a dictionarys
    track_playtime_list = [
        {
            'index': index,
            'name': track_name,
            'artist': track_artist_name,
            'total_ms_played': total_ms_played,
            'total_hours_played': total_ms_played / MS_IN_HOUR,
            'album_image_url': sp.track(track_id=spotify_track_uri.replace("spotify:track:", ""))['album']['images'][0]['url']
        }
        for index, (track_name, track_artist_name, spotify_track_uri, total_ms_played) in enumerated_query
    ]
    
    return jsonify(track_playtime_list)

# Route for getting top played tracks by time played
@db_bp.route('/history/top_tracks_by_playcount', methods=['GET'])
def get_top_tracks_by_playcount():
    if 'token_info' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    sp = get_spotify_client()

    limit = request.args.get('limit', default=10, type=int)

    query = ( # query for track name, artist and total ms played, grouped by track name to sum up total ms played, and order by total ms played descending
        db_session.query(
            StreamingHistory.master_metadata_track_name,
            StreamingHistory.master_metadata_album_artist_name,
            StreamingHistory.spotify_track_uri,
            func.count(StreamingHistory.ts).label('count_of_plays')
        )
        .filter(StreamingHistory.master_metadata_track_name.isnot(None))  # Exclude None track names
        .group_by(StreamingHistory.master_metadata_track_name, StreamingHistory.master_metadata_album_artist_name)
        .order_by(desc('count_of_plays'))
        .limit(limit) # how many top tracks to return
    )
    
    enumerated_query = enumerate(query)
    
    # Convert the result into a dictionarys
    track_playcount_list = [
        {
            'index': index,
            'name': track_name,
            'artist': track_artist_name,
            'count_of_plays': count_of_plays,
            'album_image_url': sp.track(track_id=spotify_track_uri.replace("spotify:track:", ""))['album']['images'][0]['url']
        }
        for index, (track_name, track_artist_name, spotify_track_uri, count_of_plays) in enumerated_query
    ]
    
    return jsonify(track_playcount_list)

