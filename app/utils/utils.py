import spotipy
import pandas as pd
import matplotlib.pyplot as plt
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
                'popularity': track['popularity']
            })
    return play_history

def get_liked_tracks(sp, limit=None):
    # TODO: Realize offset logic for pagination(?)
    user_id = session.get('user_id')
    cache_key = f'liked_tracks_{user_id}'
    
    liked_tracks = cache.get(cache_key)
    
    if not liked_tracks:
        liked_tracks = []
        if limit:
            results = sp.current_user_saved_tracks(limit)
        else:
            liked_tracks = []
            i = 0
            while True:
            # for i in range(1000):
                results = sp.current_user_saved_tracks(limit=50, offset=i*50)
                print(results)
                if results['items'].__len__() > 0:
                    for item in results['items']:
                        track = item['track']
                        liked_tracks.append({
                            'name': track['name'],
                            'artist': track['artists'][0]['name'],
                            'album_image_url': track['album']['images'][0]['url'],
                            'popularity': track['popularity']
                        })
                else: break
                i += 1
        # Cache the result for future use
        cache.set(cache_key, liked_tracks)
    print (len(liked_tracks))
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

