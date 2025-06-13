from flask import jsonify, request
from app.database import db_session
from app.models import StreamingHistory
from app.utils.stats_manager import StatsManager
from . import db_bp


# Record fetching
# region 

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

# Meta
@db_bp.route('/stats/<username>/calculate', methods=['POST'])
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


