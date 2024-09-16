import spotipy
import pandas as pd
from datetime import datetime

from flask import session
from flask_caching import Cache

cache = Cache(config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 1200})
# cache = Cache(config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 1})

def get_play_history(sp, limit=50):
    user_id = session.get('user_id')
    cache_key = f'play_history_{user_id}'
    
    play_history = cache.get(cache_key)
    
    
    if not play_history:
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

def get_liked_tracks(sp, limit=None, offset=None):
    user_id = session.get('user_id')
    cache_key = f'liked_tracks_{user_id}'
    
    liked_tracks = cache.get(cache_key)
    
    if not liked_tracks:
        liked_tracks = []
        if limit: # if there is a limit, get the tracks in the specified limit
            if limit > 50: # if the limit is greater than 50, get the tracks in chunks of 50
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
            else:
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
        else:
            liked_tracks = __get_full_saved_tracks(sp, user_id)
                
        cache.set(cache_key, liked_tracks)
    
    return liked_tracks


def get_top_artists(sp, time_range='medium_term', limit=50):
    # TODO: Process results
    results = sp.current_user_top_artists(time_range=time_range, limit=limit)
    return results['items']

def get_top_tracks(sp, time_range='medium_term', limit=50):
    results = sp.current_user_top_tracks(time_range=time_range, limit=limit)
    top_tracks = []
    for track in results['items']:
        top_tracks.append({
            'name': track['name'],
            'artist': track['artists'][0]['name'], # TODO: handle multiple artists
            'album_image_url': track['album']['images'][0]['url'],
            'spotify_url': track['album']['external_urls']['spotify'],
            'popularity': track['popularity']
        })
    return top_tracks

def get_tracks_by_year(sp):
    user_id = session.get('user_id')
    cache_key = f'tracks_by_year_{user_id}'
    
    tracks_by_year = cache.get(cache_key)
    
    if not tracks_by_year:
        tracks_by_year = __get_full_saved_tracks(sp, user_id)
        tracks_by_year_count = {}
        
        # drop columns that are not needed in full_saved_tracks
        # for d in tracks_by_year:
        #     for key in ['added_at', 'name', 'artist', 'album_image_url', 'spotify_url', 'popularity']:
        #         d.pop(key, None)
        
        for track in tracks_by_year:
            release_year = track["release_date"].split("-")[0]  # Extract the year
            tracks_by_year_count[release_year] = tracks_by_year_count.get(release_year, 0) + 1
            
        # cache.set(cache_key, tracks_by_year)
    return tracks_by_year_count

def __get_full_saved_tracks(sp, user_id):
    cache_key = f'full_saved_tracks_{user_id}'
    
    full_saved_tracks = cache.get(cache_key)
    
    if not full_saved_tracks:
        full_saved_tracks = []
        offset = 0
        while True:
            results = sp.current_user_saved_tracks(limit=50, offset=offset)
            if not results['items']:
                break
            for item in results['items']:
                track = item['track']
                full_saved_tracks.append({
                    # 'added_at': datetime.strptime(item['added_at'], '%Y-%m-%dT%H:%M:%S.%fZ'),
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
