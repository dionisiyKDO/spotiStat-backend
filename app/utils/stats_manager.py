from app.utils.stats_calculator import SpotifyStatsCalculator
from app.models import UserStats, StreamingHistory
from app.database import db_session
from sqlalchemy import distinct
import json

class StatsManager:
    @staticmethod
    def calculate_stats_for_user(username):
        """Calculate and save stats for a specific user"""
        calculator = SpotifyStatsCalculator(username)
        return calculator.calculate_all_stats()
    
    @staticmethod
    def get_stats_for_user(username):
        """Get pre-calculated stats for a user"""
        user_stats = db_session.query(UserStats).filter(
            UserStats.username == username
        ).first()
        
        if not user_stats:
            return None
        
        return json.loads(user_stats.stats_data)
    
    @staticmethod
    def stats_exist_for_user(username):
        """Check if stats exist for a user"""
        return db_session.query(UserStats).filter(
            UserStats.username == username
        ).first() is not None
    
    @staticmethod
    def get_stats_calculation_date(username):
        """Get when stats were last calculated for a user"""
        user_stats = db_session.query(UserStats).filter(
            UserStats.username == username
        ).first()
        
        return user_stats.calculated_at if user_stats else None

    @staticmethod
    def calculate_all_users_stats(self):
        """Calculate stats for all users who have listening history"""
        users = db_session.query(distinct(StreamingHistory.username)).all()
        
        for user_tuple in users:
            username = user_tuple[0]
            if username:
                self.calculate_user_stats_command(username)