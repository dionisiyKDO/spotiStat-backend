from flask import jsonify, session, current_app, request
from sqlalchemy import func, desc, extract
import pandas as pd

from app.blueprints.auth.routes import get_spotify_client
from app.utils.utils import *
from . import db_bp


@db_bp.route('/check_history')
def check_history():
    account_id = request.args.get('account_id')

    if not os.path.exists(f"app/data/{account_id}"):
        return jsonify({'error': 'No history found for this account'}), 404
    else:
        return jsonify({'message': 'History found for this account'})









MS_IN_HOUR = 1000 * 60 * 60

# NOW it is route for importing json files from pc, and storing them in sqllite db
# Ideally, it should be a route to accept json files from the frontend, and store them in the db
# @db_bp.route('/upload_history', methods=['POST'])
@db_bp.route('/upload_history')
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
        # db_session.query(
        #     func.date(StreamingHistory.ts).label('date'), 
        #     func.count(StreamingHistory.ts).label('play_count'),
        #     func.sum(StreamingHistory.ms_played).label('total_ms_played')  # Adding total playtime per day
        # )
        # .filter(StreamingHistory.master_metadata_track_name.ilike(f'%{track_id}%'))
        # .group_by(func.date(StreamingHistory.ts))
        # .order_by(func.date(StreamingHistory.ts))
        # .all()
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

# Route to get statistics for a specific artist including timeline data
@db_bp.route('/history/artist/<artist_name>/stats', methods=['GET'])
def get_artist_stats(artist_name):
    # Query to get daily play counts and total playtime per day for the artist
    play_counts = (
        db_session.query(
            func.date(StreamingHistory.ts).label('date'),
            func.count(StreamingHistory.ts).label('play_count'),
            func.sum(StreamingHistory.ms_played).label('total_ms_played')
        )
        .filter(StreamingHistory.master_metadata_album_artist_name == artist_name)
        .group_by(func.date(StreamingHistory.ts))
        .order_by(func.date(StreamingHistory.ts))
        .all()
    )

    # Query to get overall playtime and stats for the artist
    artist_stats = (
        db_session.query(
            func.sum(StreamingHistory.ms_played).label('total_ms_played'),
            func.count(StreamingHistory.ts).label('total_plays'),
            func.min(StreamingHistory.ts).label('first_played'),
            func.max(StreamingHistory.ts).label('last_played'),
            func.count(func.distinct(func.date(StreamingHistory.ts))).label('distinct_days_played')
        )
        .filter(StreamingHistory.master_metadata_album_artist_name == artist_name)
        .one()
    )
    
    # Error handling: If the artist has no plays, return an error response
    if not artist_stats.total_plays:
        return jsonify({'error': f'No stats available for artist: {artist_name}'}), 404

    # Convert 'first_played' and 'last_played' to datetime objects
    first_played = (
        datetime.strptime(artist_stats.first_played, '%Y-%m-%dT%H:%M:%SZ')
        if isinstance(artist_stats.first_played, str) else artist_stats.first_played
    )
    last_played = (
        datetime.strptime(artist_stats.last_played, '%Y-%m-%dT%H:%M:%SZ')
        if isinstance(artist_stats.last_played, str) else artist_stats.last_played
    )

    # Calculate additional stats
    avg_playtime = artist_stats.total_ms_played / artist_stats.total_plays if artist_stats.total_plays > 0 else 0
    total_days_played = (last_played - first_played).days if first_played and last_played else 0

    # Convert daily play counts to a timeline list
    timeline_data = [
        {"date": str(play_count[0]), "play_count": play_count[1], "total_ms_played": play_count[2]}
        for play_count in play_counts
    ]

    # Convert date times to ISO format strings for JSON output
    first_played_str = first_played.strftime('%Y-%m-%d %H:%M:%S') if first_played else None
    last_played_str = last_played.strftime('%Y-%m-%d %H:%M:%S') if last_played else None

    return jsonify({
        'artist_name': artist_name,
        'timeline_data': timeline_data,
        'total_ms_played': artist_stats.total_ms_played,
        'total_plays': artist_stats.total_plays,
        'distinct_days_played': artist_stats.distinct_days_played,
        'first_played': first_played_str,
        'last_played': last_played_str,
        'avg_playtime_per_play': avg_playtime,
        'total_days_played': total_days_played
    })

# Route to get the top N artists by playtime with optional timeline data
@db_bp.route('/history/artists/top', methods=['GET'])
def get_top_artists():
    # Get parameters from request (default to top 10 and minimum 1 hour playtime)
    top_n = int(request.args.get('limit', 10))
    min_playtime_hours = float(request.args.get('min_playtime', 1))
    
    # Convert minimum playtime to milliseconds
    min_playtime_ms = min_playtime_hours * 60 * 60 * 1000

    # Query to get the top N artists by total playtime, filtered by minimum playtime
    top_artists = (
        db_session.query(
            StreamingHistory.master_metadata_album_artist_name.label('artist_name'),
            func.sum(StreamingHistory.ms_played).label('total_ms_played'),
            func.count(StreamingHistory.ts).label('total_plays')
        )
        .group_by(StreamingHistory.master_metadata_album_artist_name)
        .having(func.sum(StreamingHistory.ms_played) >= min_playtime_ms)
        .order_by(func.sum(StreamingHistory.ms_played).desc())
        .limit(top_n)
        .all()
    )

    # If no artists found, return an empty list
    if not top_artists:
        return jsonify({'error': 'No artists found with the specified criteria'}), 404

    # Collect the artist data with optional daily timeline
    top_artists_data = []
    
    for artist in top_artists:
        # Query to get daily play counts and total playtime for this artist (for each day)
        play_counts = (
            db_session.query(
                func.date(StreamingHistory.ts).label('date'),
                func.count(StreamingHistory.ts).label('play_count'),
                func.sum(StreamingHistory.ms_played).label('total_ms_played')
            )
            .filter(StreamingHistory.master_metadata_album_artist_name == artist.artist_name)
            .group_by(func.date(StreamingHistory.ts))
            .order_by(func.date(StreamingHistory.ts))
            .all()
        )

        # Convert daily play counts to a timeline list
        timeline_data = [
            {"date": str(play_count[0]), "play_count": play_count[1], "total_ms_played": play_count[2]}
            for play_count in play_counts
        ]

        # Add artist data and timeline to the result
        top_artists_data.append({
            'artist_name': artist.artist_name,
            'total_ms_played': artist.total_ms_played,
            'total_plays': artist.total_plays,
            'timeline_data': timeline_data  # Add the timeline here
        })

    return jsonify({
        'top_n': top_n,
        'min_playtime_hours': min_playtime_hours,
        'artists': top_artists_data
    })

# Route: Fetch tracks played more than {limit_count} times or {limit_play} milliseconds
@db_bp.route('/history/played-tracks', methods=['GET'])
def fetch_played_tracks():
    """
    Fetches tracks that were played more than {limit_count} times 
    or {limit_play} milliseconds in total.

    Example: /played-tracks?limit_count=5&limit_play=100000
    """
    limit_count = request.args.get('limit_count', 0, type=int)  # Default to 0 if not provided
    limit_play = request.args.get('limit_play', 0, type=int)  # Default to 0 if not provided
    
    # Fetch tracks from StreamingHistory model where play count or total playtime exceeds the given limits
    play_counts = (
        db_session.query(
            StreamingHistory.master_metadata_track_name.label('track_name'),
            StreamingHistory.master_metadata_album_artist_name.label('artist_name'),
            StreamingHistory.spotify_track_uri.label('spotify_track_uri'),
            func.count(StreamingHistory.ts).label('play_count'),
            func.sum(StreamingHistory.ms_played).label('total_ms_played')
        )
        .filter(StreamingHistory.spotify_track_uri != None)
        .group_by(StreamingHistory.spotify_track_uri, StreamingHistory.master_metadata_track_name)
        .having(
            func.count(StreamingHistory.ts) > limit_count
        )
        .having(
            func.sum(StreamingHistory.ms_played) > limit_play
        )
        .all()
    )
    
    # Convert results to a list of dictionaries
    played_tracks = [
        {
            'track_name': track.track_name,
            'artist': track.artist_name,
            'spotify_track_uri': track.spotify_track_uri,
            'play_count': track.play_count,
            'total_ms_played': track.total_ms_played
        } for track in play_counts
    ]
    
    return jsonify(played_tracks=played_tracks)
