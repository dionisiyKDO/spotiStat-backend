"""Application settings, loaded from environment / .env (prefix ``SPOTISTAT_``)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="SPOTISTAT_", extra="ignore"
    )

    # Separate filename from the legacy Flask DB so the two never collide.
    database_url: str = "sqlite:///./app/data/spotistat.db"

    # Where per-user archive folders live: <data_dir>/<username>/*.json
    data_dir: str = "app/data"

    # Local timezone used to bucket time-based stats (hour / weekday / date).
    # The raw instant is stored in UTC; this only affects how stats are grouped.
    timezone: str = "Europe/Kyiv"

    # Glob for the Spotify "Extended Streaming History" audio files.
    audio_file_glob: str = "Streaming_History_Audio_*.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
