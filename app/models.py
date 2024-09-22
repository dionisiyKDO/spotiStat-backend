from sqlalchemy import Column, Boolean, Integer, String
from datetime import datetime, timezone
import pytz

from app.database import Base

utc_plus_3 = pytz.timezone('Etc/GMT-3')

# draft for future user profile table
# class UserProfile(Base):
#     __tablename__ = 'user_profiles'
#     spotify_id = Column(String, primary_key=True)
#     nickname = Column(String, unique=True)
#     profile_folder = Column(String)
#     def __repr__(self):
#         return f'<UserProfile {self.spotify_id} - {self.nickname}>'

class StreamingHistory(Base):
    __tablename__ = 'streaming_history'
    # TODO: timestamp should be a datetime object
    
    id = Column(Integer, primary_key=True)
    ts = Column(String(50), nullable=False)
    username = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=True)
    ms_played = Column(Integer, nullable=False)
    conn_country = Column(String(5), nullable=True)
    ip_addr_decrypted = Column(String(50), nullable=True)
    user_agent_decrypted = Column(String(255), nullable=True)
    master_metadata_track_name = Column(String(255), nullable=True)
    master_metadata_album_artist_name = Column(String(255), nullable=True)
    master_metadata_album_album_name = Column(String(255), nullable=True)
    spotify_track_uri = Column(String(255), nullable=True)
    episode_name = Column(String(255), nullable=True)
    episode_show_name = Column(String(255), nullable=True)
    spotify_episode_uri = Column(String(255), nullable=True)
    reason_start = Column(String(50), nullable=True)
    reason_end = Column(String(50), nullable=True)
    shuffle = Column(Boolean, nullable=False, default=False)
    skipped = Column(Boolean, nullable=False, default=False)
    offline = Column(Boolean, nullable=False, default=False)
    offline_timestamp = Column(Integer, nullable=True)
    incognito_mode = Column(Boolean, nullable=False, default=False)
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'ts': self.ts,
            'username': self.username,
            'platform': self.platform,
            'ms_played': self.ms_played,
            'conn_country': self.conn_country,
            'ip_addr_decrypted': self.ip_addr_decrypted,
            'user_agent_decrypted': self.user_agent_decrypted,
            'master_metadata_track_name': self.master_metadata_track_name,
            'master_metadata_album_artist_name': self.master_metadata_album_artist_name,
            'master_metadata_album_album_name': self.master_metadata_album_album_name,
            'spotify_track_uri': self.spotify_track_uri,
            'episode_name': self.episode_name,
            'episode_show_name': self.episode_show_name,
            'spotify_episode_uri': self.spotify_episode_uri,
            'reason_start': self.reason_start,
            'reason_end': self.reason_end,
            'shuffle': self.shuffle,
            'skipped': self.skipped,
            'offline': self.offline,
            'offline_timestamp': self.offline_timestamp,
            'incognito_mode': self.incognito_mode
        }
    
    def __repr__(self) -> str:
        return f"<StreamingHistory(ts={self.ts}, username={self.username}, platform={self.platform}, ms_played={self.ms_played}, conn_country={self.conn_country}, ip_addr_decrypted={self.ip_addr_decrypted}, user_agent_decrypted={self.user_agent_decrypted}, master_metadata_track_name={self.master_metadata_track_name}, master_metadata_album_artist_name={self.master_metadata_album_artist_name}, master_metadata_album_album_name={self.master_metadata_album_album_name}, spotify_track_uri={self.spotify_track_uri}, episode_name={self.episode_name}, episode_show_name={self.episode_show_name}, spotify_episode_uri={self.spotify_episode_uri}, reason_start={self.reason_start}, reason_end={self.reason_end}, shuffle={self.shuffle}, skipped={self.skipped}, offline={self.offline}, offline_timestamp={self.offline_timestamp}, incognito_mode={self.incognito_mode})>"