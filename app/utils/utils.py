import spotipy
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def get_play_history(sp, limit=50):
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
    if limit:
        results = sp.current_user_saved_tracks(limit)
    else:
        # TODO: Realize offset logic for pagination
        results = sp.current_user_saved_tracks(offset=15)
    liked_tracks = []
    for item in results['items']:
        track = item['track']
        liked_tracks.append({
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album_image_url': track['album']['images'][0]['url'],
            'popularity': track['popularity']
        })
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

