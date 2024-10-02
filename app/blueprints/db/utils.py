from flask import jsonify, session, current_app, request
from sqlalchemy import func, desc, extract
import pandas as pd

from app.blueprints.auth.routes import get_spotify_client
from app.utils.utils import *
from . import db_bp

MS_IN_HOUR = 1000 * 60 * 60

@db_bp.route('/history/<int:limit>', methods=['GET']) # limit is the number of records to return, in url for dumbcheck purposes 
def get_all_records(limit: int):
    ''' 
    Retrieve the full listening history
        limit: number of records to return
    '''
    records = db_session.query(StreamingHistory).limit(limit).all()
    return jsonify([record.to_dict() for record in records])

@db_bp.route('/history/record/<int:id>', methods=['GET'])
def get_streaming_record(id: int):
    '''
    Get specific record from listening history
        id: id of the record to return
    '''
    record = db_session.query(StreamingHistory).get(id)
    if not record:
        return jsonify({'error': f'Record with id {id} not found'}), 404
    
    return jsonify(record.to_dict())

@db_bp.route('/history/top-tracks', methods=['GET'])
def get_top_tracks():
    '''
    Get the top N tracks by play count or total listening time for a user\n
    args:
        limit: number of records to return, default - 10
        sort_by: field to sort by, either 'play_count' or default 'total_ms_played'
    '''
    limit   = request.args.get('limit', 10, type=int)
    sort_by = request.args.get('sort_by', 'total_ms_played', type=str)
    sp = get_spotify_client()
    
    sort_by = 'total_ms_played' if sort_by == 'total_ms_played' else 'play_count'
    
    top_tracks = db_session.query(
        StreamingHistory.master_metadata_track_name,
        StreamingHistory.master_metadata_album_artist_name,
        func.count(StreamingHistory.master_metadata_track_name).label('play_count'),
        func.sum(StreamingHistory.ms_played).label('total_ms_played'),
        StreamingHistory.spotify_track_uri,
    ).filter(
        StreamingHistory.master_metadata_track_name.isnot(None)
    ).group_by(
        StreamingHistory.master_metadata_track_name, 
        StreamingHistory.master_metadata_album_artist_name
    ).order_by(desc(sort_by)).limit(limit).all()

    return jsonify([{
        'index': index,
        'track_name': track[0],
        'artist': track[1],
        'play_count': track[2],
        'total_ms_played': track[3],
        'album_image_url': sp.track(track_id=track[4].replace("spotify:track:", ""))['album']['images'][0]['url']
    } for index,track in enumerate(top_tracks)])
