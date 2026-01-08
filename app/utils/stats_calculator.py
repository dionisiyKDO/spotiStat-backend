from sqlalchemy import func, desc, distinct
from sqlalchemy.orm import Session
import datetime
import json

from app.models import StreamingHistory, UserStats, User
from werkzeug.security import generate_password_hash, check_password_hash

MS_IN_DAY = 1000 * 60 * 60 * 24
MS_IN_HOUR = 1000 * 60 * 60
MS_IN_MINUTE = 1000 * 60

class SpotifyStatsCalculator:
    def __init__(self, username: str, db: Session):
        self.db = db
        self.username = username
        print(self.db, self.username)
        
    def calculate_all_stats(self):
        """Calculate all statistics for a user and save them to database"""
        stats = {
            'username': self.username,
            'calculated_at': datetime.datetime.now(datetime.timezone.utc),
            'total_listening_time': self._calculate_total_listening_time(),
            'platform_stats': self._calculate_platform_stats(),
            'most_skipped_tracks': self._calculate_most_skipped_tracks(),
            'skip_stats': self._calculate_skip_stats(),
            'end_reasons': self._calculate_end_reasons(),
            'unique_tracks_count': self._calculate_unique_tracks_count(),
            'top_artists': self._calculate_top_artists(),
            'top_tracks': self._calculate_top_tracks(),
            'listening_by_hour': self._calculate_listening_by_hour(),
            'listening_by_year': self._calculate_listening_by_year(),
            'listening_by_month': self._calculate_listening_by_month(),
            'listening_by_weekday': self._calculate_listening_by_weekday(),
            'listening_by_date': self._calculate_listening_by_date(),
            'longest_session': self._calculate_longest_listening_session(),
        }
        
        # Save to database
        self._save_stats_to_db(stats)
        return stats
    
    def _calculate_total_listening_time(self):
        """Calculate total listening time in various units"""
        total_ms = self.db.query(
            func.sum(StreamingHistory.ms_played)
        ).filter(StreamingHistory.username == self.username).scalar() or 0
        
        return {
            'total_listening_ms': total_ms,
            'total_listening_minutes': round((total_ms / MS_IN_MINUTE), 2),
            'total_listening_hours': round((total_ms / MS_IN_HOUR), 2),
            'total_listening_days': round((total_ms / MS_IN_DAY), 2),
        }
    
    def _calculate_platform_stats(self):
        """Calculate listening stats by platform"""
        platform_stats = self.db.query(
            StreamingHistory.platform,
            func.count(StreamingHistory.platform).label('play_count'),
            func.sum(StreamingHistory.ms_played).label('total_ms_played'),
        ).filter(StreamingHistory.username == self.username
        ).group_by(StreamingHistory.platform).all()

        grouped_stats = {
            'Linux': {'play_count': 0, 'total_ms_played': 0},
            'Windows': {'play_count': 0, 'total_ms_played': 0},
            'Android': {'play_count': 0, 'total_ms_played': 0},
            'Other': {'play_count': 0, 'total_ms_played': 0}
        }

        for platform in platform_stats:
            platform_name = platform[0].lower() if platform[0] else 'other'
            
            if 'linux' in platform_name:
                grouped_stats['Linux']['play_count'] += platform[1]
                grouped_stats['Linux']['total_ms_played'] += platform[2] or 0
            elif 'windows' in platform_name:
                grouped_stats['Windows']['play_count'] += platform[1]
                grouped_stats['Windows']['total_ms_played'] += platform[2] or 0
            elif 'android' in platform_name:
                grouped_stats['Android']['play_count'] += platform[1]
                grouped_stats['Android']['total_ms_played'] += platform[2] or 0
            else:
                grouped_stats['Other']['play_count'] += platform[1]
                grouped_stats['Other']['total_ms_played'] += platform[2] or 0

        return [{
            'platform': platform,
            'play_count': stats['play_count'],
            'total_ms_played': stats['total_ms_played']
        } for platform, stats in grouped_stats.items()]
    
    def _calculate_most_skipped_tracks(self, limit=50):
        """Calculate most skipped tracks"""
        skipped_tracks = self.db.query(
            StreamingHistory.master_metadata_track_name,
            StreamingHistory.master_metadata_album_artist_name,
            func.count(StreamingHistory.id).label('skip_count'),
            StreamingHistory.spotify_track_uri,
        ).filter(
            StreamingHistory.username == self.username,
            StreamingHistory.skipped == True
        ).group_by(
            StreamingHistory.master_metadata_track_name,
            StreamingHistory.master_metadata_album_artist_name
        ).order_by(desc('skip_count')).limit(limit).all()
        
        return [{
            'track_name': track[0],
            'artist': track[1],
            'skip_count': track[2],
            'spotify_track_uri': track[3],
        } for track in skipped_tracks]
    
    def _calculate_skip_stats(self):
        """Calculate skip statistics"""
        total_plays = self.db.query(func.count(StreamingHistory.id)).filter(
            StreamingHistory.username == self.username
        ).scalar() or 0
        
        skipped_tracks = self.db.query(func.count(StreamingHistory.id)).filter(
            StreamingHistory.username == self.username,
            StreamingHistory.skipped == True
        ).scalar() or 0
        
        return {
            'total_plays': total_plays,
            'skipped_tracks': skipped_tracks,
            'skip_rate': skipped_tracks / total_plays if total_plays > 0 else 0,
            'skip_percentage': skipped_tracks / total_plays * 100 if total_plays > 0 else 0
        }
    
    def _calculate_end_reasons(self):
        """Calculate end reasons statistics"""
        end_reasons = self.db.query(
            StreamingHistory.reason_end, 
            func.count(StreamingHistory.reason_end).label('count')
        ).filter(StreamingHistory.username == self.username).group_by(
            StreamingHistory.reason_end
        ).order_by(desc('count')).all()
        
        return [{
            'reason_end': reason[0],
            'count': reason[1]
        } for reason in end_reasons]
    
    def _calculate_unique_tracks_count(self):
        """Calculate unique tracks count"""
        unique_tracks = self.db.query(
            func.count(distinct(StreamingHistory.spotify_track_uri))
        ).filter(StreamingHistory.username == self.username).scalar() or 0
        
        return {'unique_tracks_count': unique_tracks}
    
    def _calculate_top_artists(self, limit=50):
        """Calculate top artists by play count and listening time"""
        top_artists = self.db.query(
            StreamingHistory.master_metadata_album_artist_name,
            func.count(StreamingHistory.id).label('play_count'),
            func.sum(StreamingHistory.ms_played).label('total_ms_played'),
            func.count(distinct(StreamingHistory.master_metadata_track_name)).label('distinct_track_count')
        ).filter(
            StreamingHistory.username == self.username
        ).group_by(
            StreamingHistory.master_metadata_album_artist_name
        ).order_by(desc('total_ms_played')).limit(limit).all()

        return [{
            'artist': artist[0],
            'play_count': artist[1],
            'total_ms_played': artist[2] or 0,
            'total_hours': round((artist[2] / MS_IN_HOUR), 2),
            'distinct_track_count': artist[3]
        } for artist in top_artists]
    
    def _calculate_top_tracks(self, limit=50):
        """Calculate top tracks by play count"""
        top_tracks = self.db.query(
            StreamingHistory.master_metadata_track_name,
            StreamingHistory.master_metadata_album_artist_name,
            func.count(StreamingHistory.id).label('play_count'),
            func.sum(StreamingHistory.ms_played).label('total_ms_played'),
            StreamingHistory.spotify_track_uri,
        ).filter(
            StreamingHistory.username == self.username
        ).group_by(
            StreamingHistory.master_metadata_track_name,
            StreamingHistory.master_metadata_album_artist_name
        ).order_by(desc('total_ms_played')).limit(limit).all()
        
        return [{
            'track_name': track[0],
            'artist': track[1],
            'play_count': track[2],
            'total_ms_played': track[3] or 0,
            'total_hours': round((track[3] / MS_IN_HOUR), 2),
            'spotify_track_uri': track[4],
        } for track in top_tracks]
    
    def _calculate_listening_by_hour(self):
        """Calculate listening patterns by hour of day"""
        from sqlalchemy import extract
        
        hourly_stats = self.db.query(
            extract('hour', StreamingHistory.ts).label('hour'),
            func.count(StreamingHistory.id).label('play_count'),
            func.sum(StreamingHistory.ms_played).label('total_ms_played'),
        ).filter(
            StreamingHistory.username == self.username
        ).group_by(extract('hour', StreamingHistory.ts)).all()
        
        return [{
            'hour': int(stat[0]) if stat[0] is not None else 0,
            'play_count': stat[1],
            'total_ms_played': stat[2] or 0,
        } for stat in hourly_stats]
    
    def _calculate_listening_by_weekday(self):
        """Calculate listening patterns by weekday"""
        
        weekday_stats = self.db.query(
            func.strftime('%w', StreamingHistory.ts).label('weekday'),
            func.count(StreamingHistory.id).label('play_count'),
            func.sum(StreamingHistory.ms_played).label('total_ms_played'),
        ).filter(
            StreamingHistory.username == self.username
        ).group_by(func.strftime('%w', StreamingHistory.ts)).all()
        
        weekday_map = {
            '0': 'Sunday',
            '1': 'Monday',
            '2': 'Tuesday',
            '3': 'Wednesday',
            '4': 'Thursday',
            '5': 'Friday',
            '6': 'Saturday',
        }
        
        return [{
            'weekday': weekday_map.get(stat[0], 'Unknown'),
            'play_count': stat[1],
            'total_ms_played': stat[2] or 0,
        } for stat in weekday_stats]
    
    def _calculate_listening_by_month(self):
        """Calculate listening patterns by month"""
        from sqlalchemy import extract
        
        monthly_stats = self.db.query(
            func.strftime('%Y-%m', StreamingHistory.ts).label('month'),
            func.count(StreamingHistory.id).label('play_count'),
            func.sum(StreamingHistory.ms_played).label('total_ms_played'),
        ).filter(
            StreamingHistory.username == self.username
        ).group_by(func.strftime('%Y-%m', StreamingHistory.ts).label('month'),
        ).order_by(func.strftime('%Y-%m', StreamingHistory.ts).label('month'),).all()
        
        return [{
            'month': stat[0],
            'play_count': stat[1],
            'total_ms_played': stat[2] or 0,
        } for stat in monthly_stats]

    def _calculate_listening_by_year(self):
        """Calculate listening patterns by year"""
        from sqlalchemy import extract
        
        monthly_stats = self.db.query(
            extract('year', StreamingHistory.ts).label('year'),
            func.count(StreamingHistory.id).label('play_count'),
            func.sum(StreamingHistory.ms_played).label('total_ms_played'),
        ).filter(
            StreamingHistory.username == self.username
        ).group_by(
            extract('year', StreamingHistory.ts)
        ).order_by('year').all()
        
        return [{
            'year': int(stat[0]) if stat[0] is not None else 0,
            'play_count': stat[1],
            'total_ms_played': stat[2] or 0,
        } for stat in monthly_stats]

    def _calculate_listening_by_date(self):
        """Calculate listening patterns by exact date (e.g. 01-02-2021)"""
        
        date_stats = self.db.query(
            func.strftime('%Y-%m-%d', StreamingHistory.ts).label('date'),
            func.count(StreamingHistory.id).label('play_count'),
            func.sum(StreamingHistory.ms_played).label('total_ms_played'),
        ).filter(
            StreamingHistory.username == self.username
        ).group_by(func.strftime('%Y-%m-%d', StreamingHistory.ts)
        ).order_by(func.strftime('%Y-%m-%d', StreamingHistory.ts)).all()
        
        return [{
            'date': stat[0],
            'play_count': stat[1],
            'total_ms_played': stat[2] or 0,
        } for stat in date_stats]
    
    def _calculate_longest_listening_session(self, gap_minutes=30):
        """Calculate the longest listening session (based on total_ms_played)"""
        time_gap_ms = gap_minutes * 60000  # Convert minutes to milliseconds

        tracks = self.db.query(
            StreamingHistory.master_metadata_track_name,
            StreamingHistory.master_metadata_album_artist_name,
            StreamingHistory.spotify_track_uri,
            StreamingHistory.ms_played,
            StreamingHistory.ts
        ).filter(
            StreamingHistory.username == self.username
        ).order_by(StreamingHistory.ts).all()

        longest_session = None
        current_session = []
        total_ms = 0
        prev_ts = None
        session_start = None

        for track_name, artist, uri, ms_played, ts in tracks:
            if isinstance(ts, str):
                ts = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ')

            if prev_ts:
                time_diff = (ts - prev_ts).total_seconds() * 1000
                if time_diff > time_gap_ms:
                    if not longest_session or total_ms > longest_session['total_ms_played']:
                        longest_session = {
                            'session_start': session_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'session_end': prev_ts.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            'total_tracks': len(current_session),
                            'total_ms_played': total_ms,
                            'tracks': current_session[:]
                        }
                    current_session = []
                    total_ms = 0
                    session_start = ts

            if not current_session:
                session_start = ts

            current_session.append({
                'track_name': track_name,
                'track_artist': artist,
                'track_uri': uri,
                'timestamp': ts.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'ms_played': ms_played
            })
            total_ms += ms_played
            prev_ts = ts

        # Check final session
        if current_session and (not longest_session or total_ms > longest_session['total_ms_played']):
            longest_session = {
                'session_start': session_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'session_end': prev_ts.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'total_tracks': len(current_session),
                'total_ms_played': total_ms,
                'tracks': current_session[:]
            }

        return longest_session or {}
    
    def _save_stats_to_db(self, stats):
        """Save calculated stats to database"""
        # If User and userstats doesn't exist
        user = self.db.query(User).filter(User.username == self.username).first()
        if not user:
            user = User(username=self.username, password_hash=generate_password_hash(self.username))
            self.db.add(user)
            self.db.commit()
        
        # Delete existing stats for this user
        self.db.query(UserStats).filter(UserStats.user == user).delete()
        
        # Create new stats record
        user_stats = UserStats(
            user=user,
            stats_data=json.dumps(stats, default=str),  # Convert datetime to string
            calculated_at=stats['calculated_at']
        )
        
        self.db.add(user_stats)
        self.db.commit()

