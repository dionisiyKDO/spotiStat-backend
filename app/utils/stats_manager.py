from app.utils.stats_calculator import SpotifyStatsCalculator
from app.models import UserStats, StreamingHistory
from sqlalchemy.orm import Session
from sqlalchemy import distinct
import json

class StatsManager:
    @staticmethod
    def calculate_stats_for_user(username: str, db: Session):
        """Calculate and save stats for a specific user"""
        calculator = SpotifyStatsCalculator(username, db)
        return calculator.calculate_all_stats()
    
    @staticmethod
    def get_stats_for_user(username: str, db: Session):
        """Get pre-calculated stats for a user"""
        user_stats = db.query(UserStats).filter(
            UserStats.username == username
        ).first()
        
        if not user_stats:
            return None
        
        return json.loads(user_stats.stats_data)
    
    @staticmethod
    def stats_exist_for_user(username: str, db: Session):
        """Check if stats exist for a user"""
        return db.query(UserStats).filter(
            UserStats.username == username
        ).first() is not None
    
    @staticmethod
    def get_stats_calculation_date(username: str, db: Session):
        """Get when stats were last calculated for a user"""
        user_stats = db.query(UserStats).filter(
            UserStats.username == username
        ).first()
        
        return user_stats.calculated_at if user_stats else None

    @staticmethod
    def calculate_all_users_stats(self, db: Session):
        """Calculate stats for all users who have listening history"""
        users = db.query(distinct(StreamingHistory.username)).all()
        # TODO: Create Users table, that ^ is insane
        
        for user_tuple in users:
            username = user_tuple[0]
            if username:
                self.calculate_user_stats_command(username)