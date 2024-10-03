import os, json
import spotipy
import pandas as pd
from datetime import datetime

from flask import session
from flask_caching import Cache
from sqlalchemy.exc import IntegrityError

from app.database import db_session, init_db, get_user_db
from app.models import StreamingHistory, User

cache = Cache(config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 1200})
# cache = Cache(config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 1})

init_db()



# read json files from pc and store them in db
def read_json_and_store_data(json_directory):
    for file_name in os.listdir(json_directory): # Iterate through the files in the specified directory
        if file_name.startswith("Streaming_History_Audio_") and file_name.endswith(".json"): # Check if the file matches the pattern 'Streaming_History_Audio_{year}.json'
            file_path = os.path.join(json_directory, file_name)
            with open(file_path, 'r', encoding='utf-8') as f: # Load JSON data from the file
                try:
                    data = json.load(f)
                    for record in data: # Iterate through each record in the JSON file
                        history = StreamingHistory( # Create a StreamingHistory instance for each record in the JSON file
                            ts=record.get('ts'),
                            username=record.get('username'),
                            platform=record.get('platform'),
                            ms_played=record.get('ms_played'),
                            conn_country=record.get('conn_country'),
                            ip_addr_decrypted=record.get('ip_addr_decrypted'),
                            user_agent_decrypted=record.get('user_agent_decrypted'),
                            master_metadata_track_name=record.get('master_metadata_track_name'),
                            master_metadata_album_artist_name=record.get('master_metadata_album_artist_name'),
                            master_metadata_album_album_name=record.get('master_metadata_album_album_name'),
                            spotify_track_uri=record.get('spotify_track_uri'),
                            episode_name=record.get('episode_name'),
                            episode_show_name=record.get('episode_show_name'),
                            spotify_episode_uri=record.get('spotify_episode_uri'),
                            reason_start=record.get('reason_start'),
                            reason_end=record.get('reason_end'),
                            shuffle=record.get('shuffle'),
                            skipped=record.get('skipped'),
                            offline=record.get('offline'),
                            offline_timestamp=record.get('offline_timestamp'),
                            incognito_mode=record.get('incognito_mode')
                        )
                        db_session.add(history) # Add the record to the session
                    db_session.commit() # Commit the records in bulk after processing the file
                    print(f"Data from {file_name} stored successfully.")
                except (json.JSONDecodeError, IntegrityError) as e:
                    print(f"Error processing {file_name}: {e}")
                    db_session.rollback()
                    return False
    return True