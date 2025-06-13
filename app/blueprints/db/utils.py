from flask import jsonify, session, current_app, request
from sqlalchemy import func, desc, extract, case, distinct
from datetime import datetime
from app.database import db_session
from app.models import StreamingHistory, UserStats
from app.utils.stats_manager import StatsManager
import pandas as pd

# from app.utils.upload_utils import *
from . import db_bp

MS_IN_DAY = 1000 * 60 * 60 * 24
MS_IN_HOUR = 1000 * 60 * 60
MS_IN_MINUTE = 1000 * 60


# region Record fetching

@db_bp.route('/history/<int:limit>', methods=['GET']) # TODO: questionable existance, but for know okay
def get_all_records(limit: int):
    ''' 
    Retrieve the listening history from head for <username>
        limit: number of records to return
    '''
    username = str(request.args.get('username', None))
    if not username:
        return jsonify({'error': 'No username provided'}), 404
    
    records = db_session.query(StreamingHistory).filter(StreamingHistory.username == username).limit(limit).all()
    return jsonify([record.to_dict() for record in records])

@db_bp.route('/history/artist/<string:artist_name>', methods=['GET'])
def get_all_records_by_artist(artist_name: str):
    '''
    Retrieve all records for <username> filtered by artist name
        artist_name: name of the artist to search for
    '''
    username = str(request.args.get('username', None))
    if not username:
        return jsonify({'error': 'No username provided'}), 404

    records = db_session.query(StreamingHistory).filter(
        (StreamingHistory.username == username) &
        (StreamingHistory.master_metadata_album_artist_name.ilike(f'%{artist_name}%'))
    ).all()
    
    if not records:
        return jsonify({'error': f'Records with artist name "{artist_name}" for user "{username}" not found'}), 404
    
    return jsonify([record.to_dict() for record in records])

@db_bp.route('/history/album/<string:album_name>', methods=['GET'])
def get_all_records_by_album(album_name):
    '''
    Retrieve all records for <username> filtered by album name
        album_name: name of the album to search for
    '''
    username = str(request.args.get('username', None))
    if not username:
        return jsonify({'error': 'No username provided'}), 404
    
    records = db_session.query(StreamingHistory).filter(
        (StreamingHistory.username == username) &
        (StreamingHistory.master_metadata_album_album_name.ilike(f'%{album_name}%')) 
    ).all()
    
    if not records:
        return jsonify({'error': f'Records with album name "{album_name}" for user "{username}" not found'}), 404
    
    return jsonify([record.to_dict() for record in records])

# endregion


# Stats routes
# region

# TODO: check if works
@db_bp.route('/stats/calculate/<username>', methods=['POST'])
def calculate_user_stats(username):
    """Trigger stats calculation for a user"""
    try:
        stats = StatsManager.calculate_stats_for_user(username)
        return jsonify({
            'message': f'Stats calculated successfully for {username}',
            'calculated_at': stats['calculated_at']
        })
    except Exception as e:
        return jsonify({'error': f'Error calculating stats: {str(e)}'}), 500

@db_bp.route('/stats/status/<username>', methods=['GET'])
def get_stats_status(username):
    """Check if stats exist for a user and when they were last calculated"""
    exists = StatsManager.stats_exist_for_user(username)
    calculation_date = StatsManager.get_stats_calculation_date(username)
    
    return jsonify({
        'stats_exist': exists,
        'last_calculated': calculation_date.isoformat() if calculation_date else None
    })

@db_bp.route('/stats/total-listening-time/<username>', methods=['GET']) # 100 to 40 / -60ms response time
def get_total_listening_time(username):
    ''' Display the total listening time in ms/min/hour/day '''
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['total_listening_time'])

@db_bp.route('/stats/platform-stats/<username>', methods=['GET']) # 140 to 40 / -100ms response time
def get_platform_stats(username):
    ''' Display the total listening time and number of plays for each platform '''
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['platform_stats'])

@db_bp.route('/stats/most-skipped-tracks/<username>', methods=['GET']) # 100 to 40 / -60ms response time
def get_most_skipped_tracks(username):
    ''' Get the most skipped tracks '''
    limit = request.args.get('limit', 10, type=int)
    
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    skipped_tracks = stats['most_skipped_tracks'][:limit]
    
    return jsonify([{
        'index': index,
        **track
    } for index, track in enumerate(skipped_tracks)])

@db_bp.route('/stats/skip-stats/<username>', methods=['GET']) # 120 to 40 / -80ms response time
def get_skip_stats(username):
    ''' Get the total number of plays and the number of skipped tracks + skip rate '''
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['skip_stats'])

@db_bp.route('/stats/end-reasons/<username>', methods=['GET']) # 150 to 40 / -110ms response time
def get_end_reasons(username):
    ''' Get the number of times each end reason occurred '''
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['end_reasons'])

@db_bp.route('/stats/unique-tracks-count/<username>', methods=['GET']) # 170 to 40 / -130ms response time
def get_unique_tracks_count(username):
    ''' Get the number of unique tracks listened to '''
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['unique_tracks_count'])

@db_bp.route('/stats/top-artists/<username>', methods=['GET'])
def get_top_artists(username):
    """Get pre-calculated top artists"""
    limit = request.args.get('limit', 10, type=int)
    
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['top_artists'][:limit])

@db_bp.route('/stats/top-tracks/<username>', methods=['GET'])
def get_top_tracks(username):
    """Get pre-calculated top tracks"""
    limit = request.args.get('limit', 10, type=int)
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['top_tracks'][:limit])

@db_bp.route('/stats/listening-by-hour/<username>', methods=['GET'])
def get_listening_by_hour(username):
    """Get pre-calculated listening patterns by hour"""
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['listening_by_hour'])

@db_bp.route('/stats/listening-by-month/<username>', methods=['GET'])
def get_listening_by_month(username):
    """Get pre-calculated listening patterns by month"""
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['listening_by_month'])

@db_bp.route('/stats/all/<username>', methods=['GET'])
def get_all_stats(username):
    """Get all pre-calculated stats for a user"""
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats)

# endregion











def process_sessions(sessions, time_gap_ms):
    ''' Helper function to process listening sessions '''
    result = []
    session = []
    previous_ts = None
    session_start_time = None
    total_ms_played = 0  # Track total playtime for each session

    for record in sessions:
        current_ts = record.ts

        # Convert current timestamp to datetime if it's a string
        if isinstance(current_ts, str):
            current_ts = datetime.strptime(current_ts, '%Y-%m-%dT%H:%M:%SZ')

        if previous_ts:
            # Calculate time difference in milliseconds between consecutive tracks
            time_diff_ms = (current_ts - previous_ts).total_seconds() * 1000

            # If time difference is greater than the specified gap, end the current session
            if time_diff_ms > time_gap_ms:
                if session:
                    # Append session details to the result before starting a new session
                    result.append({
                        'session_start': session_start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'session_end': previous_ts.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'total_tracks': len(session),
                        'total_ms_played': total_ms_played,
                        'tracks': session
                    })
                # Reset session info for a new session
                session = []
                total_ms_played = 0

        # If starting a new session, set the session start time
        if not session:
            session_start_time = current_ts

        # Add the current track to the session
        session.append({
            'track_name': record.master_metadata_track_name,
            'track_artist': record.master_metadata_album_artist_name,
            'track_uri': record.spotify_track_uri,
            'timestamp': current_ts.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'ms_played': record.ms_played
        })

        # Increment total ms played for the session
        total_ms_played += record.ms_played

        # Update previous timestamp
        previous_ts = current_ts

    # Append the last session if it exists
    if session:
        result.append({
            'session_start': session_start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'session_end': previous_ts.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'total_tracks': len(session),
            'total_ms_played': total_ms_played,
            'tracks': session
        })

    return result

@db_bp.route('/history/sessions', methods=['GET'])
def get_listening_sessions():
    ''' Get listening sessions and their statistics '''
    username = request.args.get('username', None)
    if username == None:
        return jsonify({'error': 'No username provided'}), 404
    
    time_gap = request.args.get('gap', 30, type=int)  # Gap in minutes to separate sessions
    time_gap_ms = time_gap * 60000

    # Query to get tracks in order of timestamps
    sessions = db_session.query(
        StreamingHistory.id,
        StreamingHistory.master_metadata_track_name,
        StreamingHistory.master_metadata_album_artist_name,
        StreamingHistory.spotify_track_uri,
        StreamingHistory.ms_played,
        StreamingHistory.ts
    ).filter(StreamingHistory.username == username).order_by(StreamingHistory.ts).all()

    # Process sessions using the helper function
    result = process_sessions(sessions, time_gap_ms)

    return jsonify(result)

@db_bp.route('/history/sessions/longest', methods=['GET'])
def get_longest_session():
    ''' Get the longest listening session '''
    username = request.args.get('username', None)
    if username == None:
        return jsonify({'error': 'No username provided'}), 404
    
    time_gap = request.args.get('gap', 30, type=int)  # Gap in minutes to separate sessions
    time_gap_ms = time_gap * 60000

    # Query to get tracks in order of timestamps
    sessions = db_session.query(
        StreamingHistory.id,
        StreamingHistory.master_metadata_track_name,
        StreamingHistory.master_metadata_album_artist_name,
        StreamingHistory.spotify_track_uri,
        StreamingHistory.ms_played,
        StreamingHistory.ts
    ).filter(StreamingHistory.username == username).order_by(StreamingHistory.ts).all()

    # Process sessions
    all_sessions = process_sessions(sessions, time_gap_ms)

    # Find the longest session based on total_ms_played
    if all_sessions:
        longest_session = max(all_sessions, key=lambda s: s['total_ms_played'])
        return jsonify(longest_session)

    return jsonify({'error': 'No sessions found'}), 404


# Trends
# region

@db_bp.route('/history/hourly-trends', methods=['GET'])
def get_hourly_trends():
    ''' Get hourly listening statistics '''
    username = request.args.get('username', None)
    if username == None:
        return jsonify({'error': 'No username provided'}), 404
    
    hourly_trends = db_session.query(
        func.extract('hour', StreamingHistory.ts).label('hour'),
        func.count(StreamingHistory.id).label('play_count'),
        func.sum(StreamingHistory.ms_played).label('total_ms_played')
    ).filter(StreamingHistory.username == username
    ).group_by('hour').order_by('hour').all()

    return jsonify([{
        'hour': int(trend.hour),
        'play_count': trend.play_count,
        'total_ms_played': trend.total_ms_played
    } for trend in hourly_trends])

@db_bp.route('/history/weekly-trends', methods=['GET'])
def get_weekly_trends():
    ''' Get weekly listening statistics '''
    username = request.args.get('username', None)
    if username == None:
        return jsonify({'error': 'No username provided'}), 404
    
    daily_trends = db_session.query(
        func.strftime('%w', StreamingHistory.ts).label('day_of_week'),  # Get day of the week (0 = Sunday, ..., 6 = Saturday)
        func.count(StreamingHistory.id).label('play_count'),
        func.sum(StreamingHistory.ms_played).label('total_ms_played')
    ).filter(StreamingHistory.username == username
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
    ''' Get daily listening statistics '''
    username = request.args.get('username', None)
    if username == None:
        return jsonify({'error': 'No username provided'}), 404
    
    daily_trends = db_session.query(
        func.strftime('%Y-%m-%d', StreamingHistory.ts).label('day'),  # Use strftime for SQLite date formatting
        func.count(StreamingHistory.id).label('play_count'),
        func.sum(StreamingHistory.ms_played).label('total_ms_played')
    ).filter(StreamingHistory.username == username
    ).group_by(func.strftime('%Y-%m-%d', StreamingHistory.ts)
    ).order_by(func.strftime('%Y-%m-%d', StreamingHistory.ts)
    ).all()

    return jsonify([{
        'day': trend.day,  # The day is already formatted as a string
        'play_count': trend.play_count,
        'total_ms_played': trend.total_ms_played
    } for trend in daily_trends])

# endregion

# endregion
# TODO: add year sorting
# @db_bp.route('/history/top-tracks', methods=['GET'])
# def get_top_tracks():
#     '''
#     Get the top N tracks by play count or total listening time for a user\n
#     args:
#         limit: number of records to return, default - 10
#         sort_by: field to sort by, either 'play_count' or default 'total_ms_played'
#         year: filter tracks by a specific year
#         month: filter tracks by a specific month (1-12)
#         date: filter tracks by a specific date (format: YYYY-MM-DD)
#         artist: filter tracks by a specific artist name
#     '''
#     username = request.args.get('username', None)
#     if username == None:
#         return jsonify({'error': 'No username provided'}), 404
    
#     limit   = request.args.get('limit', 10, type=int)
#     sort_by = request.args.get('sort_by', 'total_ms_played', type=str)
#     year    = request.args.get('year', type=int)
#     month   = request.args.get('month', type=int)
#     date    = request.args.get('date', type=str)
#     artist  = request.args.get('artist', type=str)

#     sp = get_spotify_client()
    
#     # Sort by total listening time or play count
#     sort_by = 'total_ms_played' if sort_by == 'total_ms_played' else 'play_count'

#     # Base query
#     query = db_session.query(
#         StreamingHistory.master_metadata_track_name,
#         StreamingHistory.master_metadata_album_artist_name,
#         func.count(StreamingHistory.master_metadata_track_name).label('play_count'),
#         func.sum(StreamingHistory.ms_played).label('total_ms_played'),
#         StreamingHistory.spotify_track_uri,
#     ).filter(
#         StreamingHistory.master_metadata_track_name.isnot(None) and 
#         StreamingHistory.username == username
#     )

#     # Apply filters
#     if year:
#         query = query.filter(extract('year', StreamingHistory.ts) == year)

#     if month:
#         query = query.filter(extract('month', StreamingHistory.ts) == month)

#     if date:
#         try:
#             date_obj = datetime.strptime(date, '%Y-%m-%d')
#             query = query.filter(extract('year', StreamingHistory.ts) == date_obj.year,
#                                  extract('month', StreamingHistory.ts) == date_obj.month,
#                                  extract('day', StreamingHistory.ts) == date_obj.day)
#         except ValueError:
#             return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

#     if artist:
#         query = query.filter(StreamingHistory.master_metadata_album_artist_name.ilike(f"%{artist}%"))

#     # Group, order, and limit the query
#     top_tracks = query.group_by(
#         StreamingHistory.master_metadata_track_name, 
#         StreamingHistory.master_metadata_album_artist_name
#     ).order_by(desc(sort_by)).limit(limit).all()

#     # Fetch album image from Spotify API and prepare the response
#     return jsonify([{
#         'index': index,
#         'track_name': track[0],
#         'artist': track[1],
#         'play_count': track[2],
#         'total_ms_played': track[3],
#         'album_image_url': sp.track(track_id=track[4].replace("spotify:track:", ""))['album']['images'][0]['url'],
#         'spotify_url': sp.track(track_id=track[4].replace("spotify:track:", ""))['album']['external_urls']['spotify']
#     } for index, track in enumerate(top_tracks)])


# @db_bp.route('/history/top-tracks', methods=['GET'])
# def get_top_tracks():
#     '''
#     Get the top N tracks by play count or total listening time for a user\n
#     args:
#         limit: number of records to return, default - 10
#         sort_by: field to sort by, either 'play_count' or default 'total_ms_played'
#     '''
#     limit   = request.args.get('limit', 10, type=int)
#     sort_by = request.args.get('sort_by', 'total_ms_played', type=str)
#     sp = get_spotify_client()
    
#     sort_by = 'total_ms_played' if sort_by == 'total_ms_played' else 'play_count'
    
#     top_tracks = db_session.query(
#         StreamingHistory.master_metadata_track_name,
#         StreamingHistory.master_metadata_album_artist_name,
#         func.count(StreamingHistory.master_metadata_track_name).label('play_count'),
#         func.sum(StreamingHistory.ms_played).label('total_ms_played'),
#         StreamingHistory.spotify_track_uri,
#     ).filter(
#         StreamingHistory.master_metadata_track_name.isnot(None)
#     ).group_by(
#         StreamingHistory.master_metadata_track_name, 
#         StreamingHistory.master_metadata_album_artist_name
#     ).order_by(desc(sort_by)).limit(limit).all()

#     return jsonify([{
#         'index': index,
#         'track_name': track[0],
#         'artist': track[1],
#         'play_count': track[2],
#         'total_ms_played': track[3],
#         'album_image_url': sp.track(track_id=track[4].replace("spotify:track:", ""))['album']['images'][0]['url']
#     } for index,track in enumerate(top_tracks)])

