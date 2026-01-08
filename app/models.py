# app/models.py
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import json

from app.database import Base

import pytz
utc_plus_3 = pytz.timezone('Etc/GMT-3')


# User based on local username and password
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    stats = relationship(
        "UserStats",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,  # one-to-one; remove if need history
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserStats(Base):
    __tablename__ = 'user_stats'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # one-to-one; remove if many stats per user
    )
    
    user = relationship("User", back_populates="stats")
    
    stats_data = Column(Text, nullable=False)  # JSON string of all stats
    calculated_at = Column(DateTime, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.user.username,
            'stats_data': json.loads(self.stats_data),
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }


class StreamingHistory(Base):
    __tablename__ = 'streaming_history'
    
    id = Column(Integer, primary_key=True, index=True)
    ts = Column(DateTime, nullable=False, index=True)
    username = Column(String(255), nullable=False, index=True)  
    platform = Column(String(50), nullable=True)
    ms_played = Column(Integer, nullable=False)
    conn_country = Column(String(5), nullable=True)
    ip_addr = Column(String(50), nullable=True)
    master_metadata_track_name = Column(String(255), nullable=True)
    master_metadata_album_artist_name = Column(String(255), nullable=True)
    master_metadata_album_album_name = Column(String(255), nullable=True)
    spotify_track_uri = Column(String(255), nullable=True)
    episode_name = Column(String(255), nullable=True)
    episode_show_name = Column(String(255), nullable=True)
    spotify_episode_uri = Column(String(255), nullable=True)
    audiobook_title = Column(String(255), nullable=True)
    audiobook_uri = Column(String(255), nullable=True)
    audiobook_chapter_uri = Column(String(255), nullable=True)
    audiobook_chapter_title = Column(String(255), nullable=True)
    reason_start = Column(String(50), nullable=True)
    reason_end = Column(String(50), nullable=True)
    shuffle = Column(Boolean, nullable=False, default=False)
    skipped = Column(Boolean, nullable=False, default=False)
    offline = Column(Boolean, nullable=False, default=False)
    offline_timestamp = Column(DateTime, nullable=True)
    incognito_mode = Column(Boolean, nullable=False, default=False)
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'ts': self.ts,
            'username': self.username,
            'platform': self.platform,
            'ms_played': self.ms_played,
            'conn_country': self.conn_country,
            'ip_addr': self.ip_addr,
            'master_metadata_track_name': self.master_metadata_track_name,
            'master_metadata_album_artist_name': self.master_metadata_album_artist_name,
            'master_metadata_album_album_name': self.master_metadata_album_album_name,
            'spotify_track_uri': self.spotify_track_uri,
            'episode_name': self.episode_name,
            'episode_show_name': self.episode_show_name,
            'spotify_episode_uri': self.spotify_episode_uri,
            'audiobook_title': self.audiobook_title,
            'audiobook_uri': self.audiobook_uri,
            'audiobook_chapter_uri': self.audiobook_chapter_uri,
            'audiobook_chapter_title': self.audiobook_chapter_title,
            'reason_start': self.reason_start,
            'reason_end': self.reason_end,
            'shuffle': self.shuffle,
            'skipped': self.skipped,
            'offline': self.offline,
            'offline_timestamp': self.offline_timestamp,
            'incognito_mode': self.incognito_mode
        }
    
    def __repr__(self) -> str:
        return f"<StreamingHistory(ts={self.ts}, username={self.username}, platform={self.platform}, ms_played={self.ms_played}, conn_country={self.conn_country}, ip_addr={self.ip_addr}, master_metadata_track_name={self.master_metadata_track_name}, master_metadata_album_artist_name={self.master_metadata_album_artist_name}, master_metadata_album_album_name={self.master_metadata_album_album_name}, spotify_track_uri={self.spotify_track_uri}, episode_name={self.episode_name}, episode_show_name={self.episode_show_name}, spotify_episode_uri={self.spotify_episode_uri}, audiobook_title={self.audiobook_title}, audiobook_uri={self.audiobook_uri}, audiobook_chapter_uri={self.audiobook_chapter_uri}, audiobook_chapter_title={self.audiobook_chapter_title}, reason_start={self.reason_start}, reason_end={self.reason_end}, shuffle={self.shuffle}, skipped={self.skipped}, offline={self.offline}, offline_timestamp={self.offline_timestamp}, incognito_mode={self.incognito_mode})>"