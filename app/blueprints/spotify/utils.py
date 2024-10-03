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


def __get_full_saved_tracks(sp, user_id):
    cache_key = f'full_saved_tracks_{user_id}'
    full_saved_tracks = cache.get(cache_key)
    
    
    if not full_saved_tracks: # If the cache is empty, fetch all saved tracks
        full_saved_tracks = []
        offset = 0
        while True: # Go through all saved tracks until all tracks are fetched
            results = sp.current_user_saved_tracks(limit=50, offset=offset)
            if not results['items']: # If there are no more saved tracks, break the loop
                break
            for item in results['items']: # Iterate through each saved track
                track = item['track']
                full_saved_tracks.append({
                    'added_at': item['added_at'],
                    'release_date': track['album']['release_date'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album_image_url': track['album']['images'][0]['url'],
                    'spotify_url': track['album']['external_urls']['spotify'],
                    'popularity': track['popularity']
                })
            offset += 50
        cache.set(cache_key, full_saved_tracks)
    return full_saved_tracks

# Get last {limit} played tracks
def get_play_history(sp, limit=50):
    user_id = session.get('user_id')
    cache_key = f'play_history_{user_id}'
    play_history = cache.get(cache_key)
    
    
    if not play_history: # If the cache is empty, fetch all play history
        results = sp.current_user_recently_played(limit=limit)
        
        play_history = []
        for item in results['items']:
            track = item['track']
            play_history.append({
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'album_image_url': track['album']['images'][0]['url'],
                'duration_ms': track['duration_ms'],
                'played_at': datetime.strptime(item['played_at'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                'spotify_url': track['album']['external_urls']['spotify'],
                'popularity': track['popularity']
            })
    return play_history

# get {limit} liked tracks, if limit is None, get all liked tracks
# TODO: refactor this function, offset logic is not good
def get_liked_tracks(sp, limit=None, offset=0):
    user_id = session.get('user_id')
    cache_key = f'liked_tracks_{user_id}'
    liked_tracks = cache.get(cache_key)
    
    
    if not liked_tracks:
        liked_tracks = []
        if limit: # if there is a limit, get the tracks in the specified limit
            if limit > 50: # if the limit is greater than 50, get the tracks in chunks of 50 multiple times, starting from offset 0
                offset = 0
                while True: # loop until all tracks are fetched in the specified limit
                    if offset >= limit:
                        break
                    results = sp.current_user_saved_tracks(limit=50, offset=offset)
                    if not results['items']:
                        break
                    for item in results['items']:
                        track = item['track']
                        liked_tracks.append({
                            'name': track['name'],
                            'artist': track['artists'][0]['name'],
                            'album_image_url': track['album']['images'][0]['url'],
                            'spotify_url': track['album']['external_urls']['spotify'],
                            'popularity': track['popularity']
                        })
                    offset += 50
            else: # if the limit is less than or equal to 50, get the tracks in one go
                results = sp.current_user_saved_tracks(limit=limit, offset=offset)
                for item in results['items']:
                    track = item['track']
                    liked_tracks.append({
                        'name': track['name'],
                        'artist': track['artists'][0]['name'],
                        'album_image_url': track['album']['images'][0]['url'],
                        'spotify_url': track['album']['external_urls']['spotify'],
                        'popularity': track['popularity']
                    })
        else: # if there is no limit, get all saved tracks
            liked_tracks = __get_full_saved_tracks(sp, user_id)
        cache.set(cache_key, liked_tracks)
    return liked_tracks

# get {limit} top artists
def get_top_artists(sp, time_range='medium_term', limit=50):
    # TODO: caching(?)
    top_artists = sp.current_user_top_artists(time_range=time_range, limit=limit)
    
    return top_artists['items']

# get {limit} top tracks
def get_top_tracks(sp, time_range='medium_term', limit=50):
    top_tracks = sp.current_user_top_tracks(time_range=time_range, limit=limit)
    
    results = []
    for track in top_tracks['items']:
        results.append({
            'name': track['name'],
            'artist': track['artists'][0]['name'], # TODO: handle multiple artists
            'album_image_url': track['album']['images'][0]['url'],
            'spotify_url': track['album']['external_urls']['spotify'],
            'popularity': track['popularity']
        })
    return results

# get tracks count by each year
def get_tracks_by_year(sp):
    user_id = session.get('user_id')
    cache_key = f'tracks_by_year_{user_id}'
    tracks_by_year_count = cache.get(cache_key)
    
    
    if not tracks_by_year_count: # if the cache is empty, fetch all saved tracks
        tracks_by_year = __get_full_saved_tracks(sp, user_id)
        tracks_by_year_count = {}
        
        for track in tracks_by_year: # iterate through each track
            release_year = track["release_date"].split("-")[0]  # Extract the year
            tracks_by_year_count[release_year] = tracks_by_year_count.get(release_year, 0) + 1 # add the count for each year
    
        tracks_by_year_count = [{'release_date': year, 'count': count} for year, count in tracks_by_year_count.items()] # make "0: {'release_date': '2021', 'count': 1}" from "{'2021': 1}"
        cache.set(cache_key, tracks_by_year_count)
    return tracks_by_year_count

# get saved tracks by filter, rn only filter by year, can add more filters later
def select_saved_tracks(sp, year = None):
    user_id = session.get('user_id')
    cache_key = f'search_saved_tracks_{user_id}{("_" + year) if year else ""}'
    results = cache.get(cache_key)
    
    if not results: # if the cache is empty, fetch all saved tracks
        results = __get_full_saved_tracks(sp, user_id)
        
        if year: # if a year is specified, filter the results
            results = [track for track in results if track['release_date'].split("-")[0] == year]
            
        # can add more filters here
        # if filter:
        #     results = 
        
        cache.set(cache_key, results)
    return results
