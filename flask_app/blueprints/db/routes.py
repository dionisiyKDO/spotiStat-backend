from flask import jsonify, request
from sqlalchemy import func, desc
from datetime import datetime

from flask_app.utils.stats_manager import StatsManager
from flask_app.utils.upload_utils import read_json_and_store_data
from flask_app.models import StreamingHistory
from flask_app.database import db_session
from . import db_bp

MS_IN_DAY = 1000 * 60 * 60 * 24
MS_IN_HOUR = 1000 * 60 * 60
MS_IN_MINUTE = 1000 * 60

# Record fetching
# region 

@db_bp.route('/history/<username>/<int:limit>', methods=['GET']) # TODO: questionable existance, but for now okay
def get_all_records(username: str, limit: int):
    ''' 
    Retrieve the listening history from head for <username>
        limit: number of records to return
    '''
    records = db_session.query(StreamingHistory).filter(StreamingHistory.username == username).limit(limit).all()
    return jsonify([record.to_dict() for record in records])

@db_bp.route('/history/<username>/artist/<string:artist_name>', methods=['GET'])
def get_all_records_by_artist(username: str, artist_name: str):
    '''
    Retrieve all records for <username> filtered by artist name
        artist_name: name of the artist to search for
    '''
    records = db_session.query(StreamingHistory).filter(
        (StreamingHistory.username == username) &
        (StreamingHistory.master_metadata_album_artist_name.ilike(f'%{artist_name}%'))
    ).all()
    
    if not records:
        return jsonify({'error': f'Records with artist name "{artist_name}" for user "{username}" not found'}), 404

@db_bp.route('/history/<username>/album/<string:album_name>', methods=['GET'])
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

# Meta
@db_bp.route('/stats/<username>/save_files', methods=['GET'])
def save_stats_to_files(username):
    """Trigger saving stats to files for a user"""
    try:
        read_json_and_store_data(f'app/data/{username}', 'dionisiy')
        return jsonify({'message': f'Stats files saved successfully for {username}'})
    except Exception as e:
        return jsonify({'error': f'Error saving stats files: {str(e)}'}), 500

@db_bp.route('/stats/<username>/calculate', methods=['GET'])
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

@db_bp.route('/stats/<username>/status', methods=['GET'])
def get_stats_status(username):
    """Check if stats exist for a user and when they were last calculated"""
    exists = StatsManager.stats_exist_for_user(username)
    calculation_date = StatsManager.get_stats_calculation_date(username)
    
    return jsonify({
        'stats_exist': exists,
        'last_calculated': calculation_date.isoformat() if calculation_date else None
    })

# Numbers
@db_bp.route('/stats/<username>/total-listening-time', methods=['GET']) # 100 to 40 / -60ms response time
def get_total_listening_time(username):
    ''' Display the total listening time in ms/min/hour/day '''
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['total_listening_time'])

@db_bp.route('/stats/<username>/platform-stats', methods=['GET']) # 140 to 40 / -100ms response time
def get_platform_stats(username):
    ''' Display the total listening time and number of plays for each platform '''
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['platform_stats'])

@db_bp.route('/stats/<username>/most-skipped-tracks', methods=['GET']) # 100 to 40 / -60ms response time
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

@db_bp.route('/stats/<username>/skip-stats', methods=['GET']) # 120 to 40 / -80ms response time
def get_skip_stats(username):
    ''' Get the total number of plays and the number of skipped tracks + skip rate '''
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['skip_stats'])

@db_bp.route('/stats/<username>/end-reasons', methods=['GET']) # 150 to 40 / -110ms response time
def get_end_reasons(username):
    ''' Get the number of times each end reason occurred '''
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['end_reasons'])

@db_bp.route('/stats/<username>/unique-tracks-count', methods=['GET']) # 170 to 40 / -130ms response time
def get_unique_tracks_count(username):
    ''' Get the number of unique tracks listened to '''
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['unique_tracks_count'])

@db_bp.route('/stats/<username>/top-artists', methods=['GET'])
def get_top_artists(username):
    """Get pre-calculated top artists"""
    limit = request.args.get('limit', 10, type=int)
    
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['top_artists'][:limit])

@db_bp.route('/stats/<username>/top-tracks', methods=['GET'])
def get_top_tracks(username):
    """Get pre-calculated top tracks"""
    limit = request.args.get('limit', 10, type=int)
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['top_tracks'][:limit])

@db_bp.route('/stats/<username>/listening-by-hour', methods=['GET'])  # 240 to 40 / -200ms response time
def get_listening_by_hour(username):
    """Get pre-calculated listening patterns by hour"""
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['listening_by_hour'])

@db_bp.route('/stats/<username>/listening-by-month', methods=['GET'])
def get_listening_by_month(username):
    """Get pre-calculated listening patterns by month"""
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['listening_by_month'])

@db_bp.route('/stats/<username>/listening-by-year', methods=['GET'])
def get_listening_by_year(username):
    """Get pre-calculated listening patterns by year"""
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['listening_by_year'])

@db_bp.route('/stats/<username>/listening-by-weekday', methods=['GET']) # 210 to 40 / -170ms response time
def get_listening_by_weekday(username):
    """Get pre-calculated listening patterns by weekday"""
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['listening_by_weekday'])

@db_bp.route('/stats/<username>/listening-by-date', methods=['GET']) # 280-340 to 70-160 / -170ms response time
def get_listening_by_date(username):
    """Get pre-calculated listening patterns by date"""
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['listening_by_date'])

@db_bp.route('/stats/<username>/longest-session', methods=['GET']) # 2300 to 40-90 / -2210ms response time
def get_longest_session(username):
    """Get pre-calculated listening patterns by date"""
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats['longest_session'])

@db_bp.route('/stats/<username>/all', methods=['GET'])
def get_all_stats(username):
    """Get all pre-calculated stats for a user"""
    stats = StatsManager.get_stats_for_user(username)
    if not stats:
        return jsonify({'error': 'Stats not found. Please calculate stats first.'}), 404
    
    return jsonify(stats)

# endregion



@db_bp.route('/stats/<username>/listened-tracks', methods=['GET'])
def get_most_tracks(username):
    """Get all pre-calculated stats for a user"""
    top_tracks = db_session.query(
        StreamingHistory.master_metadata_track_name,
        StreamingHistory.master_metadata_album_artist_name,
        func.count(StreamingHistory.id).label('play_count'),
        func.sum(StreamingHistory.ms_played).label('total_ms_played'),
        StreamingHistory.spotify_track_uri,
    ).filter(
        (StreamingHistory.username == username) &
        (StreamingHistory.master_metadata_track_name != 0) # filtering episodes/podcasts
    ).group_by(
        StreamingHistory.master_metadata_track_name,
        StreamingHistory.master_metadata_album_artist_name
    ).having(
        func.sum(StreamingHistory.ms_played) > MS_IN_MINUTE * 10 # 10 minutes
    ).order_by(desc('total_ms_played')).all()
    
    return jsonify([{
        'track_name': track[0],
        'artist': track[1],
        'play_count': track[2],
        'total_ms_played': track[3] or 0,
        'total_hours': round(((track[3] or 0) / MS_IN_HOUR), 2),
        'spotify_track_uri': track[4],
    } for track in top_tracks])

@db_bp.route('/stats/<username>/track/<track_id>', methods=['GET'])
def get_track_stats(username, track_id):
    track_uri = f"spotify:track:{track_id}"
    base_filter = (
        (StreamingHistory.username == username) &
        (StreamingHistory.spotify_track_uri == track_uri)
    )
    
    # Get overall track statistics
    # aka: everything_else
    overall_stats = (
        db_session.query(
            func.sum(StreamingHistory.ms_played).label('total_ms_played'),
            func.count(StreamingHistory.ts).label('total_plays'),
            func.min(StreamingHistory.ts).label('first_played'),
            func.max(StreamingHistory.ts).label('last_played'),
            func.count(func.distinct(func.date(StreamingHistory.ts))).label('distinct_days_played')
        )
        .filter(base_filter)
        .one()
    )
    
    if not overall_stats.total_plays:
        return jsonify({'error': 'No stats available for this track'}), 404

    # Get daily play stats and overall track stats in one query
    # aka: timeline_data
    daily_stats = (
        db_session.query(
            func.date(StreamingHistory.ts).label('date'),
            func.count(StreamingHistory.ts).label('play_count'),
            func.sum(StreamingHistory.ms_played).label('total_ms_played')
        )
        .filter(base_filter)
        .group_by(func.date(StreamingHistory.ts))
        .order_by(func.date(StreamingHistory.ts))
        .all()
    )

    # Format response data
    timeline_data = [
        {
            "date": str(day.date),
            "play_count": day.play_count,
            "total_ms_played": day.total_ms_played
        }
        for day in daily_stats
    ]

    avg_playtime = (
        overall_stats.total_ms_played / overall_stats.total_plays 
        if overall_stats.total_plays > 0 else 0
    )
    
    # calculate most certain track length
    # group play instances by ms_played, count the number of that number appearing
    #   sort by most frequent, and it is most certain the track that started and ended naturally
    estimated_track_length = (
        db_session.query(
            StreamingHistory.ms_played,
            func.count(StreamingHistory.ms_played).label('count')
        )
        .filter(
            (StreamingHistory.username == username) &
            (StreamingHistory.spotify_track_uri == track_uri) &
            (StreamingHistory.reason_end == 'trackdone')
        )
        .group_by(StreamingHistory.ms_played)
        .order_by(desc(func.count(StreamingHistory.ms_played)))
        .first()
    )
    
    # Format datetime strings
    first_played = (
        datetime.strptime(overall_stats.first_played, '%Y-%m-%dT%H:%M:%SZ')
        if isinstance(overall_stats.first_played, str) else overall_stats.first_played
    )
    last_played = (
        datetime.strptime(overall_stats.last_played, '%Y-%m-%dT%H:%M:%SZ')
        if isinstance(overall_stats.last_played, str) else overall_stats.last_played
    )
    
    first_played_str = first_played.strftime('%Y-%m-%d %H:%M:%S') if first_played else None
    last_played_str = last_played.strftime('%Y-%m-%d %H:%M:%S') if last_played else None

    return jsonify({
        'track_id': track_id,
        'timeline_data': timeline_data,
        'total_ms_played': overall_stats.total_ms_played,
        'total_plays': overall_stats.total_plays,
        'distinct_days_played': overall_stats.distinct_days_played,
        'first_played': first_played_str,
        'last_played': last_played_str,
        'avg_playtime_per_play': avg_playtime,
        'song_length': estimated_track_length.ms_played,
    })


@db_bp.route('/stats/<username>/listened-artists', methods=['GET'])
def get_most_artists(username):
    """Get all pre-calculated stats for a user"""
    top_artists = db_session.query(
        StreamingHistory.master_metadata_album_artist_name,
        func.count(StreamingHistory.id).label('play_count'),
        func.sum(StreamingHistory.ms_played).label('total_ms_played'),
        StreamingHistory.spotify_track_uri,
    ).filter(
        StreamingHistory.username == username
    ).group_by(
        StreamingHistory.master_metadata_album_artist_name
    ).having(
        func.sum(StreamingHistory.ms_played) > MS_IN_MINUTE * 10 # 10 minutes
    ).order_by(desc('total_ms_played')).all()
    
    return jsonify([{
        'artist': artist[0],
        'play_count': artist[1],
        'total_ms_played': artist[2] or 0,
        'total_hours': round(((artist[2] or 0) / MS_IN_HOUR), 2)
    } for artist in top_artists])

@db_bp.route('/stats/<username>/artist/<artist_name>', methods=['GET'])
def get_artist_stats(username, artist_name):
    base_filter = (
        (StreamingHistory.username == username) &
        (StreamingHistory.master_metadata_album_artist_name == artist_name)
    )
    
    # Get overall artist statistics
    overall_stats = (
        db_session.query(
            func.sum(StreamingHistory.ms_played).label('total_ms_played'),
            func.count(StreamingHistory.ts).label('total_plays'),
            func.min(StreamingHistory.ts).label('first_played'),
            func.max(StreamingHistory.ts).label('last_played'),
            func.count(func.distinct(func.date(StreamingHistory.ts))).label('distinct_days_played')
        )
        .filter(base_filter)
        .one()
    )
    
    if not overall_stats.total_plays:
        return jsonify({'error': f'No stats available for artist: {artist_name}'}), 404
    
    # Get daily play stats
    daily_stats = (
        db_session.query(
            func.date(StreamingHistory.ts).label('date'),
            func.count(StreamingHistory.ts).label('play_count'),
            func.sum(StreamingHistory.ms_played).label('total_ms_played')
        )
        .filter(base_filter)
        .group_by(func.date(StreamingHistory.ts))
        .order_by(func.date(StreamingHistory.ts))
        .all()
    )
    
    # Format timeline data
    timeline_data = [
        {
            "date": str(day.date),
            "play_count": day.play_count,
            "total_ms_played": day.total_ms_played
        }
        for day in daily_stats
    ]
    
    # Calculate average playtime
    avg_playtime = (
        overall_stats.total_ms_played / overall_stats.total_plays
        if overall_stats.total_plays > 0 else 0
    )
    
    # Format datetime strings
    first_played = (
        datetime.strptime(overall_stats.first_played, '%Y-%m-%dT%H:%M:%SZ')
        if isinstance(overall_stats.first_played, str) else overall_stats.first_played
    )
    last_played = (
        datetime.strptime(overall_stats.last_played, '%Y-%m-%dT%H:%M:%SZ')
        if isinstance(overall_stats.last_played, str) else overall_stats.last_played
    )
    
    first_played_str = first_played.strftime('%Y-%m-%d %H:%M:%S') if first_played else None
    last_played_str = last_played.strftime('%Y-%m-%d %H:%M:%S') if last_played else None
    
    return jsonify({
        'artist_name': artist_name,
        'timeline_data': timeline_data,
        'total_ms_played': overall_stats.total_ms_played,
        'total_plays': overall_stats.total_plays,
        'distinct_days_played': overall_stats.distinct_days_played,
        'first_played': first_played_str,
        'last_played': last_played_str,
        'avg_playtime_per_play': avg_playtime
    })

@db_bp.route('/stats/<username>/artist/<artist_name>/listened-tracks', methods=['GET'])
def get_artists_tracks(username, artist_name):
    """Get all pre-calculated stats for a user"""
    top_tracks = db_session.query(
        StreamingHistory.master_metadata_track_name,
        func.count(StreamingHistory.id).label('play_count'),
        func.sum(StreamingHistory.ms_played).label('total_ms_played'),
        StreamingHistory.spotify_track_uri,
    ).filter(
        (StreamingHistory.username == username) &
        (StreamingHistory.master_metadata_album_artist_name == artist_name)
    ).group_by(
        StreamingHistory.master_metadata_track_name
    ).order_by(desc('total_ms_played')).all()
    
    return jsonify([{
        'track_name': track[0],
        'play_count': track[1],
        'total_ms_played': track[2] or 0,
        'total_hours': round(((track[2] or 0) / MS_IN_HOUR), 2),
        'spotify_track_uri': track[3],
    } for track in top_tracks])

