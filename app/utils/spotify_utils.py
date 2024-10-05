from app.utils.utils import *


def get_play_history(sp, limit=50):
    '''
    Fetch the user's recent play history.

    Args:
        sp: Authenticated Spotipy client.
        limit: The number of tracks to retrieve.

    Returns:
        list: List of recently played tracks.
    '''
    user_id = get_user_id()
    cache_key = f'play_history_{user_id}'
    play_history = cache.get(cache_key)
    
    if not play_history: # If the cache is empty, fetch all play history
        results = sp.current_user_recently_played(limit=limit)
        play_history = []
        
        for item in results['items']:
            play_history.append(process_track(item))
            
        
        cache_results(cache_key, play_history)
    return play_history

def fetch_full_saved_tracks(sp):
    '''
    Fetch all saved tracks from Spotify for the current user.

    Args:
        sp: Authenticated Spotipy client.

    Returns:
        list: List of all saved tracks.
    '''
    user_id = get_user_id()
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
                full_saved_tracks.append(process_track(item))
                
            offset += 50
        
        cache_results(cache_key, full_saved_tracks)
    
    return full_saved_tracks

def get_liked_tracks(sp, limit=None, offset=0):
    '''
    Fetch the user's liked/saved tracks.

    Args:
        sp: Authenticated Spotipy client.
        limit: Optional limit of how many tracks to return.
        offset: Offset for pagination.

    Returns:
        list: List of liked/saved tracks.
    '''
    user_id = get_user_id()
    cache_key = f'liked_tracks_{user_id}_{limit}_{offset}'
    liked_tracks = cache.get(cache_key)
    
    if not liked_tracks:
        liked_tracks = []
        if limit: # if there is a limit, get the tracks in the specified limit
            while offset < limit:
                batch = sp.current_user_saved_tracks(limit=min(50, limit - offset), offset=offset)
                if not batch['items']:
                    break
                
                liked_tracks.extend([process_track(item) for item in batch['items']])
                offset += 50
        else: # if there is no limit, get all saved tracks
            liked_tracks = fetch_full_saved_tracks(sp)
        
        cache_results(cache_key, liked_tracks)

    return liked_tracks

def get_top_artists(sp, time_range='medium_term', limit=50):
    '''
    Fetch the user's top artists.

    Args:
        sp: Authenticated Spotipy client.
        time_range: The time range to retrieve the top artists ('short_term', 'medium_term', 'long_term').
        limit: The number of top artists to retrieve.

    Returns:
        list: List of top artists.
    '''
    user_id = get_user_id()
    cache_key = f'top_artists_{user_id}_{time_range}'
    top_artists = cache.get(cache_key)
    
    if not top_artists:
        top_artists = sp.current_user_top_artists(time_range=time_range, limit=limit)['items']
        cache_results(cache_key, top_artists)
    
    return top_artists

def get_top_tracks(sp, time_range='medium_term', limit=50):
    '''
    Fetch the user's top tracks.

    Args:
        sp: Authenticated Spotipy client.
        time_range: The time range to retrieve the top tracks ('short_term', 'medium_term', 'long_term').
        limit: The number of top tracks to retrieve.

    Returns:
        list: List of top tracks.
    '''
    user_id = get_user_id()
    cache_key = f'top_tracks_{user_id}_{time_range}'
    top_tracks = cache.get(cache_key)
    
    if not top_tracks:
        tracks = sp.current_user_top_tracks(time_range=time_range, limit=limit)['items']
        top_tracks = [process_track({'track': track}) for track in tracks]
        cache_results(cache_key, top_tracks)
    
    return top_tracks


def get_tracks_by_year(sp):
    '''
    Fetch saved tracks grouped by their release year.

    Args:
        sp: Authenticated Spotipy client.

    Returns:
        list: List of dictionaries containing 'release_date' and track count per year.
    '''
    user_id = get_user_id()
    cache_key = f'tracks_by_year_{user_id}'
    tracks_by_year_count = cache.get(cache_key)
    
    if not tracks_by_year_count:
        tracks = fetch_full_saved_tracks(sp)
        tracks_by_year_count = {}
        
        for track in tracks: # iterate through each track
            release_year = track["release_date"].split("-")[0]  # Extract the year
            tracks_by_year_count[release_year] = tracks_by_year_count.get(release_year, 0) + 1 # add the count for each year
    
        tracks_by_year_count = [{'release_date': year, 'count': count} for year, count in tracks_by_year_count.items()] # make "0: {'release_date': '2021', 'count': 1}" from "{'2021': 1}"
        cache_results(cache_key, tracks_by_year_count)

    return tracks_by_year_count

def select_saved_tracks(sp, year = None):
    '''
    Select saved tracks based on filtering criteria (currently only year).

    Args:
        sp: Authenticated Spotipy client.
        year: Optional year to filter by.

    Returns:
        list: Filtered list of saved tracks.
    '''
    user_id = get_user_id()
    cache_key = f'search_saved_tracks_{user_id}_{year}'
    results = cache.get(cache_key)
    
    if not results:
        results = fetch_full_saved_tracks(sp)
        
        if year: # if a year is specified, filter the results
            results = [track for track in results if track['release_date'].split("-")[0] == year]
            
        # can add more filters here
        # if filter:
        #     results = 
        
        cache_results(cache_key, results)
    
    return results
