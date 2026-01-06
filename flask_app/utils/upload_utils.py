import os 
import json
import logging
from datetime import datetime
# logging.basicConfig(level=logging.INFO)

from sqlalchemy.exc import IntegrityError

from flask_app.database import db_session, init_db
from flask_app.models import StreamingHistory, User

init_db()

### Store json file to db ###
# region

def store_streaming_history(data, username):
    '''
    Store streaming history data in the database.
    
    Args:
        data (list): List of streaming history records.
    '''
    
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
    #         # fields here
    #     ))
    # db_session.bulk_save_objects(histories)
    # db_session.commit()

def process_json_file(file_path, username):
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
            store_streaming_history(data, username) # save to db
            logging.info(f"Data from {os.path.basename(file_path)} stored successfully.")
            return True
    except (json.JSONDecodeError, IntegrityError) as e:
        logging.error(f"Error processing {os.path.basename(file_path)}: {e}")
        db_session.rollback()
        return False

def read_json_and_store_data(json_directory, username):
    '''Start processing all JSONS'''
    # TODO: checks on folder existing
    # TODO: sorted checing folders, so records would bed stored chronologically
    
    print(json_directory)
    success = True
    for file_name in os.listdir(json_directory): # Iterate through the files in the specified directory
        if file_name.startswith("Streaming_History_Audio_") and file_name.endswith(".json"): # Check if the file matches the pattern 'Streaming_History_Audio_{year}.json'
            file_path = os.path.join(json_directory, file_name)
            print('start to process:', file_path)
            if not process_json_file(file_path, username): # start processing file
                success = False
    return success

# endregion

if __name__ == "__main__":
    read_json_and_store_data('./app/data/dionisiy', 'dionisiy')