import os 
import json
import logging
from datetime import datetime
# logging.basicConfig(level=logging.INFO)

from flask import session
from flask_caching import Cache

from sqlalchemy.exc import IntegrityError

from app.config import Config
from app.database import db_session, init_db
from app.models import StreamingHistory, User

# Think about using redis for caching
# Think about updating timer for cache when i use specific cached data
cache = Cache(config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': Config.CACHE_DEFAULT_TIMEOUT})
# cache = Cache(config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 1})

init_db()

### Helper Functions ###
# region

def get_username():
    '''Helper function to retrieve username from the session.'''
    return session.get('username')

def process_track(item):
    '''
    Process a track item returned by Spotify API and extract relevant details.
    
    Args:
        item: A single track object returned by the Spotify API.

    Returns:
        dict: Processed track details like name, artist, album image, etc.
    '''
    track = item['track']
    return {
        'name': track['name'],
        'artist': track['artists'][0]['name'], # TODO: handle multiple artists
        'album_image_url': track['album']['images'][0]['url'],
        'spotify_url': track['album']['external_urls']['spotify'],
        'popularity': track['popularity'],
        'duration_ms': track['duration_ms'],
        'release_date': track['album']['release_date'],
        'added_at': datetime.strptime(track['added_at'], Config.str_datetime_format) if 'added_at' in track else None,
        'played_at': datetime.strptime(track['played_at'], Config.str_datetime_format) if 'played_at' in track else None, # For saved tracks, includes when it was added
    }

def cache_results(cache_key, data, timeout=3600):
    '''
    Helper function to cache results for a specified timeout.

    Args:
        cache_key: Cache key to store the data.
        data: Data to cache.
        timeout: Duration in seconds to cache the data (default: 3600 seconds).
    '''
    cache.set(cache_key, data, timeout)

# endregion


### Store json file to db ###
# region

def store_streaming_history(data):
    '''
    Store streaming history data in the database.
    
    Args:
        data (list): List of streaming history records.
    '''
    username = get_username()
    
    for record in data:
        history = StreamingHistory(
            ts=record.get('ts'),
            username=username,
            platform=record.get('platform'),
            ms_played=record.get('ms_played'),
            conn_country=record.get('conn_country'),
            ip_addr=record.get('ip_addr'),
            master_metadata_track_name=record.get('master_metadata_track_name'),
            master_metadata_album_artist_name=record.get('master_metadata_album_artist_name'),
            master_metadata_album_album_name=record.get('master_metadata_album_album_name'),
            spotify_track_uri=record.get('spotify_track_uri'),
            episode_name=record.get('episode_name'),
            episode_show_name=record.get('episode_show_name'),
            spotify_episode_uri=record.get('spotify_episode_uri'),
            audiobook_title=record.get('audiobook_title'),
            audiobook_uri=record.get('audiobook_uri'),
            audiobook_chapter_uri=record.get('audiobook_chapter_uri'),
            audiobook_chapter_title=record.get('audiobook_chapter_title'),
            reason_start=record.get('reason_start'),
            reason_end=record.get('reason_end'),
            shuffle=record.get('shuffle'),
            skipped=record.get('skipped'),
            offline=record.get('offline'),
            offline_timestamp=record.get('offline_timestamp'),
            incognito_mode=record.get('incognito_mode')
        )
        db_session.add(history)
    db_session.commit()
    
    # maybe faster using bulk save
    # """
    # Store streaming history data in bulk for performance optimization.
    # """
    # histories = []
    # for record in data:
    #     histories.append(StreamingHistory(
    #         # your fields here
    #     ))
    # db_session.bulk_save_objects(histories)
    # db_session.commit()

def process_json_file(file_path):
    '''
    Process a single JSON file and store the data in the database.
    
    Args:
        file_path (str): The path to the JSON file to process.
    
    Returns:
        bool: True if the process is successful, False otherwise.
    '''
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f) # load data
            store_streaming_history(data) # save to db
            logging.info(f"Data from {os.path.basename(file_path)} stored successfully.")
            return True
    except (json.JSONDecodeError, IntegrityError) as e:
        logging.error(f"Error processing {os.path.basename(file_path)}: {e}")
        db_session.rollback()
        return False

def read_json_and_store_data(json_directory):
    '''Start processing all JSONS'''
    # TODO: checks on folder existing
    # TODO: sorted checing folders, so records would bed stored chronologically
    
    
    if not get_username():
        print("Tried uploading history without logging in")
        return False
    
    
    print(json_directory)
    success = True
    for file_name in os.listdir(json_directory): # Iterate through the files in the specified directory
        if file_name.startswith("Streaming_History_Audio_") and file_name.endswith(".json"): # Check if the file matches the pattern 'Streaming_History_Audio_{year}.json'
            file_path = os.path.join(json_directory, file_name)
            print('start to process:', file_path)
            if not process_json_file(file_path): # start processing file
                success = False
    return success

# endregion
