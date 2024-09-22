from flask import jsonify, session, current_app, request
from sqlalchemy import func, desc, extract
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
    record = db_session.query(StreamingHistory).get(id)
    if not record:
        return jsonify({'error': f'Record with id {id} not found'}), 404
    
    return jsonify(record.to_dict())

# Route for getting top played tracks by time played
@db_bp.route('/history/top_tracks_by_playtime', methods=['GET'])
def get_top_played_tracks():
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

@db_bp.route('/history/track/<track_id>/stats', methods=['GET'])
def get_track_stats(track_id):
    # Strip the "spotify:track:" prefix from the URI for both queries
    track_uri = f"spotify:track:{track_id}"
    
    # Query to get play count and total playtime (ms_played) per day for the track
    play_counts = (
        db_session.query(
            func.date(StreamingHistory.ts).label('date'), 
            func.count(StreamingHistory.ts).label('play_count'),
            func.sum(StreamingHistory.ms_played).label('total_ms_played')  # Adding total playtime per day
        )
        .filter(StreamingHistory.spotify_track_uri == track_uri)
        .group_by(func.date(StreamingHistory.ts))
        .order_by(func.date(StreamingHistory.ts))
        .all()
    )

    # Query to get total playtime (ms_played) and other interesting stats
    track_stats = (
        db_session.query(
            func.sum(StreamingHistory.ms_played).label('total_ms_played'),
            func.count(StreamingHistory.ts).label('total_plays'),
            func.min(StreamingHistory.ts).label('first_played'),
            func.max(StreamingHistory.ts).label('last_played'),
            func.count(func.distinct(func.date(StreamingHistory.ts))).label('distinct_days_played')
        )
        .filter(StreamingHistory.spotify_track_uri == track_uri)
        .one()
    )
    
    # Error handling: If the track was never played, return an error response
    if not track_stats.total_plays:
        return jsonify({'error': 'No stats available for this track'}), 404

    # Convert 'first_played' and 'last_played' to datetime objects if they are strings
    first_played = (
        datetime.strptime(track_stats.first_played, '%Y-%m-%dT%H:%M:%SZ')
        if isinstance(track_stats.first_played, str) else track_stats.first_played
    )
    last_played = (
        datetime.strptime(track_stats.last_played, '%Y-%m-%dT%H:%M:%SZ')
        if isinstance(track_stats.last_played, str) else track_stats.last_played
    )
    
    # Calculate additional stats
    avg_playtime = track_stats.total_ms_played / track_stats.total_plays if track_stats.total_plays > 0 else 0
    total_days_played = (last_played - first_played).days if first_played and last_played else 0
    
    # Query to get most frequent playtime (hour)
    most_frequent_playtime = (
        db_session.query(
            extract('hour', StreamingHistory.ts).label('hour'),
            func.count(StreamingHistory.ts).label('play_count')
        )
        .filter(StreamingHistory.spotify_track_uri == track_uri)
        .group_by(extract('hour', StreamingHistory.ts))
        .order_by(func.count(StreamingHistory.ts).desc())
        .limit(1)
        .one()
    )

    # Convert play_counts to a list of dictionaries with both play count and total playtime
    timeline_data = [
        {"date": str(play_count[0]), "play_count": play_count[1], "total_ms_played": play_count[2]}
        for play_count in play_counts
    ]

    # Convert date times to ISO format strings for JSON output
    first_played_str = first_played.strftime('%Y-%m-%d %H:%M:%S') if first_played else None
    last_played_str = last_played.strftime('%Y-%m-%d %H:%M:%S') if last_played else None

    return jsonify({
        'track_id': track_id,
        'timeline_data': timeline_data,
        'total_ms_played': track_stats.total_ms_played,
        'total_plays': track_stats.total_plays,
        'distinct_days_played': track_stats.distinct_days_played,
        'first_played': first_played_str,
        'last_played': last_played_str,
        'avg_playtime_per_play': avg_playtime,
        'total_days_played': total_days_played,
        'most_frequent_play_hour': most_frequent_playtime.hour if most_frequent_playtime else None,
        'most_frequent_play_count': most_frequent_playtime.play_count if most_frequent_playtime else 0
    })
