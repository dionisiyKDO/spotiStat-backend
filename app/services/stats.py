# app/services/stats.py
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, desc, distinct
from sqlalchemy.orm import Session
import datetime
import json

from app.models import StreamingHistory, UserStats, User
from app.services.calculators.general_stats import GeneralStatsCalculator

MS_IN_DAY = 1000 * 60 * 60 * 24
MS_IN_HOUR = 1000 * 60 * 60
MS_IN_MINUTE = 1000 * 60

class StatsService:
    def __init__(self, db: Session):
        self.db = db

    def get_stats_for_user(username: str, force_refresh: bool, db: Session):
        """Get pre-calculated stats for a user"""
        user = db.query(User).filter(User.username == username).first()
        if user:
            user_stats = db.query(UserStats).filter(
                UserStats.user == user
            ).first()
        
            if not user_stats or force_refresh:
                return GeneralStatsCalculator(username, db).calculate_all_stats()
            
            return json.loads(user_stats.stats_data)
        else:
            return None
    
    # TODO: is this method needed? it returns stats anyways, why not use get_stats_for_user()
    def stats_exist_for_user(username: str, db: Session):
        """Check if stats exist for a user"""
        user = db.query(User).filter(User.username == username).first()
        if user:
            return db.query(UserStats).filter(
                UserStats.user == user
            ).first() is not None
        else: 
            return False
     
    # TODO: think about thi method
    def calculate_all_users_stats(self, db: Session):
        """Calculate stats for all users who have listening history"""
        users = db.query(distinct(StreamingHistory.username)).all()
        # TODO: Create Users table, that ^ is insane
        
        for user_tuple in users:
            username = user_tuple[0]
            if username:
                self.calculate_user_stats_command(username)

    # TODO: Refactor this methods. they doo too much + add pydantic
    def get_track_details(self, username: str, track_id: str):
        """Calculates detailed stats for a specific track on the fly."""
        track_uri = f"spotify:track:{track_id}"
        
        # Create base filters
        base_filter = (
            (StreamingHistory.username == username) &
            (StreamingHistory.spotify_track_uri == track_uri)
        )

        # The Logic
        overall_stats = (
            self.db.query(
                func.sum(StreamingHistory.ms_played).label('total_ms_played'),
                func.count(StreamingHistory.ts).label('total_plays'),
                func.min(StreamingHistory.ts).label('first_played'),
                func.max(StreamingHistory.ts).label('last_played'),
                func.count(func.distinct(func.date(StreamingHistory.ts))).label('distinct_days_played')
            )
            .filter(base_filter)
            .first()
        )

        if not overall_stats or not overall_stats.total_plays:
            return None  # Return Python None, let the Router handle the 404

        # Get daily play stats and overall track stats in one query
        # aka: timeline_data
        daily_stats = (
            self.db.query(
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
            self.db.query(
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

        # Return a clean dictionary (or Pydantic model later)
        return {
            'track_id': track_id,
            'timeline_data': timeline_data,
            'total_ms_played': overall_stats.total_ms_played,
            'total_plays': overall_stats.total_plays,
            'distinct_days_played': overall_stats.distinct_days_played,
            'first_played': first_played_str,
            'last_played': last_played_str,
            'avg_playtime_per_play': avg_playtime,
            'song_length': estimated_track_length.ms_played,
        }
    
    def get_most_tracks(self, username: str):
        top_tracks = self.db.query(
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
        
        return [{
            'track_name': track[0],
            'artist': track[1],
            'play_count': track[2],
            'total_ms_played': track[3] or 0,
            'total_hours': round(((track[3] or 0) / MS_IN_HOUR), 2),
            'spotify_track_uri': track[4],
        } for track in top_tracks]
    
    def get_most_artists(self, username: str):
        """Get all pre-calculated stats for a user"""
        top_artists = self.db.query(
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
        
        return [{
            'artist': artist[0],
            'play_count': artist[1],
            'total_ms_played': artist[2] or 0,
            'total_hours': round(((artist[2] or 0) / MS_IN_HOUR), 2)
        } for artist in top_artists]

    def get_artist_stats(self, username: str, artist_name: str):
        base_filter = (
            (StreamingHistory.username == username) &
            (StreamingHistory.master_metadata_album_artist_name == artist_name)
        )
        
        # Get overall artist statistics
        overall_stats = (
            self.db.query(
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
            return None
        
        # Get daily play stats
        daily_stats = (
            self.db.query(
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
        
        return {
            'artist_name': artist_name,
            'timeline_data': timeline_data,
            'total_ms_played': overall_stats.total_ms_played,
            'total_plays': overall_stats.total_plays,
            'distinct_days_played': overall_stats.distinct_days_played,
            'first_played': first_played_str,
            'last_played': last_played_str,
            'avg_playtime_per_play': avg_playtime
        }

    def get_artists_tracks(self, username: str, artist_name: str):
        """Get all pre-calculated stats for a user"""
        top_tracks = self.db.query(
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
        
        return [{
            'track_name': track[0],
            'play_count': track[1],
            'total_ms_played': track[2] or 0,
            'total_hours': round(((track[2] or 0) / MS_IN_HOUR), 2),
            'spotify_track_uri': track[3],
        } for track in top_tracks]

