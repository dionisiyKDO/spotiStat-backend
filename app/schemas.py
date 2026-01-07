# app/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class StreamingHistoryCreate(BaseModel):
    ts: datetime
    username: str
    platform: str
    ms_played: int
    conn_country: str
    ip_addr: Optional[str] = None
    master_metadata_track_name: Optional[str] = None
    master_metadata_album_artist_name: Optional[str] = None
    master_metadata_album_album_name: Optional[str] = None
    spotify_track_uri: Optional[str] = None
    episode_name: Optional[str]
    episode_show_name: Optional[str]
    spotify_episode_uri: Optional[str]
    audiobook_title: Optional[str] = None
    audiobook_uri: Optional[str] = None
    audiobook_chapter_uri: Optional[str] = None
    audiobook_chapter_title: Optional[str] = None
    reason_start: Optional[str] = None
    reason_end: Optional[str] = None
    shuffle: Optional[bool] = None
    skipped: Optional[bool] = None
    offline: Optional[bool] = None
    offline_timestamp: Optional[datetime] = None
    incognito_mode: Optional[bool] = None
    
    class Config:
        from_attributes = True