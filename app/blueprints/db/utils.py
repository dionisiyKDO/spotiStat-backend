from flask import jsonify, session, current_app, request
from sqlalchemy import func, desc, extract, case
import pandas as pd

from app.blueprints.auth.routes import get_spotify_client
from app.utils.utils import *
from . import db_bp

MS_IN_DAY = 1000 * 60 * 60 * 24
MS_IN_HOUR = 1000 * 60 * 60
MS_IN_MINUTE = 1000 * 60

# fetch records
# region 

@db_bp.route('/history/<int:limit>', methods=['GET']) # limit is the number of records to return, in url for dumbcheck purposes 
def get_all_records(limit: int):
    ''' 
    Retrieve the listening history from head
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

@db_bp.route('/history/artist/<string:artist_name>', methods=['GET'])
def get_by_artist(artist_name: str):
    '''
    Retrieve all records filtered by artist name
        artist_name: name of the artist to search for
    '''
    records = db_session.query(StreamingHistory).filter(
        StreamingHistory.master_metadata_album_artist_name.ilike(f'%{artist_name}%')
    ).all()
    if not records:
        return jsonify({'error': f'Records with artist name "{artist_name}" not found'}), 404
    
    return jsonify([record.to_dict() for record in records])

# endregion

# analyze data
# region

@db_bp.route('/history/total-listening-time', methods=['GET'])
def get_total_listening_time():
    ''' Display the total listening time in ms/min/hour/day '''
    total_ms = db_session.query(func.sum(StreamingHistory.ms_played)).scalar()
    total_minutes = total_ms / MS_IN_MINUTE
    total_hours = total_ms / MS_IN_HOUR
    total_days = total_ms / MS_IN_DAY
    
    return jsonify({
        'total_listening_ms': total_ms,
        'total_listening_minutes': total_minutes,
        'total_listening_hours': total_hours,
        'total_listening_days': total_days,
        })

@db_bp.route('/history/platform-stats', methods=['GET'])
def get_platform_stats():
    ''' Display the total listening time and number of plays for each platform '''
    platform_stats = db_session.query(
        StreamingHistory.platform,
        func.count(StreamingHistory.platform).label('play_count'),
        func.sum(StreamingHistory.ms_played).label('total_ms_played'),
    ).group_by(StreamingHistory.platform).all()

    grouped_stats = {
        'Linux': {'play_count': 0, 'total_ms_played': 0},
        'Windows': {'play_count': 0, 'total_ms_played': 0},
        'Android': {'play_count': 0, 'total_ms_played': 0},
        'Other': {'play_count': 0, 'total_ms_played': 0}
    }

    # Iterate over the results to group by platform category
    for platform in platform_stats:
        platform_name = platform[0].lower()  # Normalize to lowercase for matching

        if 'linux' in platform_name:
            grouped_stats['Linux']['play_count'] += platform[1]
            grouped_stats['Linux']['total_ms_played'] += platform[2]
        elif 'windows' in platform_name:
            grouped_stats['Windows']['play_count'] += platform[1]
            grouped_stats['Windows']['total_ms_played'] += platform[2]
        elif 'android' in platform_name:
            grouped_stats['Android']['play_count'] += platform[1]
            grouped_stats['Android']['total_ms_played'] += platform[2]
        else:
            grouped_stats['Other']['play_count'] += platform[1]
            grouped_stats['Other']['total_ms_played'] += platform[2]

    # Prepare the response in the desired format
    return jsonify([{
        'platform': platform,
        'play_count': stats['play_count'],
        'total_ms_played': stats['total_ms_played']
    } for platform, stats in grouped_stats.items()])

@db_bp.route('/history/skip-stats', methods=['GET'])
def get_skip_stats():
    total_plays = db_session.query(func.count(StreamingHistory.id)).scalar()
    skipped_tracks = db_session.query(func.count(StreamingHistory.id)).filter_by(skipped=True).scalar()
    return jsonify({
        'total_plays': total_plays,
        'skipped_tracks': skipped_tracks,
        'skip_rate': skipped_tracks / total_plays if total_plays > 0 else 0,
        'skip_percentage': skipped_tracks / total_plays * 100 if total_plays > 0 else 0
    })

@db_bp.route('/history/weekly-trends', methods=['GET'])
def get_weekly_trends():
    daily_trends = db_session.query(
        func.strftime('%w', StreamingHistory.ts).label('day_of_week'),  # Get day of the week (0 = Sunday, ..., 6 = Saturday)
        func.count(StreamingHistory.id).label('play_count'),
        func.sum(StreamingHistory.ms_played).label('total_ms_played')
    ).group_by(func.strftime('%w', StreamingHistory.ts)
    ).order_by(func.strftime('%w', StreamingHistory.ts)
    ).all()

    days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    return jsonify([{
        'day_of_week': days_of_week[int(trend.day_of_week)],  # Convert day number to a readable day name
        'play_count': trend.play_count,
        'total_ms_played': trend.total_ms_played
    } for trend in daily_trends])


@db_bp.route('/history/daily-trends', methods=['GET'])
def get_daily_trends():
    daily_trends = db_session.query(
        func.strftime('%Y-%m-%d', StreamingHistory.ts).label('day'),  # Use strftime for SQLite date formatting
        func.count(StreamingHistory.id).label('play_count'),
        func.sum(StreamingHistory.ms_played).label('total_ms_played')
    ).group_by(func.strftime('%Y-%m-%d', StreamingHistory.ts)
    ).order_by(func.strftime('%Y-%m-%d', StreamingHistory.ts)
    ).all()

    return jsonify([{
        'day': trend.day,  # The day is already formatted as a string
        'play_count': trend.play_count,
        'total_ms_played': trend.total_ms_played
    } for trend in daily_trends])


# endregion

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
