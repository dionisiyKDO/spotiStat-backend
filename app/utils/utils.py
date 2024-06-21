import spotipy
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def get_play_history(sp, limit=50):
    results = sp.current_user_recently_played(limit=limit)
    # return results['items']
    
    play_history = []
    for item in results['items']:
        track = item['track']
        play_history.append({
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album_image_url': track['album']['images'][0]['url'],
            'duration_ms': track['duration_ms'],
            # 'played_at': item['played_at'],
            'played_at': datetime.strptime(item['played_at'], '%Y-%m-%dT%H:%M:%S.%fZ'),
            'popularity': track['popularity']
        })
    return play_history

def get_liked_tracks(sp, limit=50):
    results = sp.current_user_saved_tracks(limit)
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



def get_top_tracks(sp, time_range='medium_term', limit=50):
    results = sp.current_user_top_tracks(time_range=time_range, limit=limit)
    return results['items']

def plot_interest_curve(sp):
    history = get_play_history(sp)
    df = pd.DataFrame(history)
    df['played_at'] = pd.to_datetime(df['played_at'])
    df.set_index('played_at', inplace=True)
    df['count'] = 1
    df = df.groupby('name').resample('M').sum().reset_index()

    plt.figure(figsize=(10, 6))
    for track in df['name'].unique():
        track_df = df[df['name'] == track]
        plt.plot(track_df['played_at'], track_df['count'], label=track)
    plt.title('Interest Curve for Tracks')
    plt.xlabel('Month')
    plt.ylabel('Number of Plays')
    plt.legend()
    plt.show()
