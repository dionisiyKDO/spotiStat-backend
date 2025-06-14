from flask import jsonify, session, current_app, request
from sqlalchemy import func, desc, extract
from datetime import datetime
import pandas as pd
import os

# from app.blueprints.auth.routes import get_spotify_client
from app.utils.upload_utils import read_json_and_store_data
from app.models import StreamingHistory, User
from app.database import db_session
from . import db_bp

MS_IN_HOUR = 1000 * 60 * 60


@db_bp.route('/history/track/<track_id>/stats', methods=['GET'])
def get_track_stats(track_id):
    username = str(request.args.get('username', None))
    if username is None:
        return jsonify({'error': 'No username provided'}), 404
    
    track_uri = f"spotify:track:{track_id}"
    
    # Query to get play_count and total_playtime (ms_played) per day for the track
    play_counts = (
        db_session.query(
            func.date(StreamingHistory.ts).label('date'), 
            func.count(StreamingHistory.ts).label('play_count'),
            func.sum(StreamingHistory.ms_played).label('total_ms_played')  # Adding total playtime per day
        )
        .filter(
            (StreamingHistory.username == username) &
            (StreamingHistory.spotify_track_uri == track_uri))                      # by track uri
            # (StreamingHistory.master_metadata_track_name.ilike(f'%{track_id}%'))  # by track name (different versions of the same track)
        .group_by(func.date(StreamingHistory.ts))
        .order_by(func.date(StreamingHistory.ts))
        .all()
    )

    # Query to get total_playtime (ms_played) and other interesting stats
    # TODO: maybe get that info from query that already made - play_counts
    track_stats = (
        db_session.query(
            func.sum(StreamingHistory.ms_played).label('total_ms_played'),
            func.count(StreamingHistory.ts).label('total_plays'),
            func.min(StreamingHistory.ts).label('first_played'),
            func.max(StreamingHistory.ts).label('last_played'),
            func.count(func.distinct(func.date(StreamingHistory.ts))).label('distinct_days_played')
        )
        .filter((StreamingHistory.username == username) &
                (StreamingHistory.spotify_track_uri == track_uri))                      # by track uri
                # (StreamingHistory.master_metadata_track_name.ilike(f'%{track_id}%'))  # by track name (different versions of the same track)
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
    
    # Query to get most frequent playtime (hour)
    most_frequent_playtime = (
        db_session.query(
            extract('hour', StreamingHistory.ts).label('hour'),
            func.count(StreamingHistory.ts).label('play_count')
        )
        .filter((StreamingHistory.spotify_track_uri == track_uri) &
                (StreamingHistory.username == username))
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
        'most_frequent_play_hour': most_frequent_playtime.hour if most_frequent_playtime else None,
        'most_frequent_play_count': most_frequent_playtime.play_count if most_frequent_playtime else 0
    })

# Route to get statistics for a specific artist including timeline data
@db_bp.route('/history/artist/<artist_name>/stats', methods=['GET'])
def get_artist_stats(artist_name):
    username = str(request.args.get('username', None))
    print('requested history/artist/<artist_name>/stats : with username = ', username)
    if username is None:
        return jsonify({'error': 'No username provided'}), 404
    
    # Query to get daily play counts and total playtime per day for the artist
    play_counts = (
        db_session.query(
            func.date(StreamingHistory.ts).label('date'),
            func.count(StreamingHistory.ts).label('play_count'),
            func.sum(StreamingHistory.ms_played).label('total_ms_played')
        )
        .filter((StreamingHistory.master_metadata_album_artist_name == artist_name) &
                (StreamingHistory.username == username))
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
        .filter((StreamingHistory.master_metadata_album_artist_name == artist_name) &
                (StreamingHistory.username == username))
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
