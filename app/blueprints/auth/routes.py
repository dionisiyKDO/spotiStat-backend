from flask import redirect, request, session, jsonify
from spotipy.oauth2 import SpotifyOAuth
import spotipy

from app.utils.utils import *
from app.config import Config
from . import auth_bp

scope = "user-library-read user-read-email user-read-recently-played user-top-read"

# Check session status route
@auth_bp.route('/session')
def session_status():
    token_info = session.get('token_info', None)
    account_id = session.get('account_id', None)
    custom_id = session.get('custom_id', None)
    logged_in = token_info is not None and account_id is not None
    if custom_id:
        return jsonify({'logged_in': logged_in, 'account_id': custom_id})
    else:
        return jsonify({'logged_in': logged_in, 'account_id': account_id})

# Route for initiating Spotify login
@auth_bp.route('/login')
def login():
    sp_oauth = SpotifyOAuth(
        client_id=Config.SPOTIPY_CLIENT_ID,
        client_secret=Config.SPOTIPY_CLIENT_SECRET,
        redirect_uri=Config.SPOTIPY_REDIRECT_URI,
        scope=scope
    )
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

# Spotify OAuth callback after login
@auth_bp.route('/callback')
def callback():
    sp_oauth = SpotifyOAuth(
        client_id=Config.SPOTIPY_CLIENT_ID,
        client_secret=Config.SPOTIPY_CLIENT_SECRET,
        redirect_uri=Config.SPOTIPY_REDIRECT_URI,
        scope=scope # permissions needed for the app
    )
    # clear session, get authorization code and exchange it for an access token
    session.clear()
    code = request.args.get('code') # Get the authorization code from the URL
    token_info = sp_oauth.get_access_token(code) # Exchange the authorization code for an access token
    
    # Use the access token to get user information
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_info = sp.current_user()
    spotify_user_id = user_info['id']

    # Check if this Spotify user is already in the database
    user = User.query.filter_by(spotify_user_id=spotify_user_id).first()
    
    if user: # User exists, get their accountId
        account_id = user.spotify_user_id
        custom_id = user.custom_id
    else: # User does not exist, create a new account
        user = User( # TODO: think of what to add here
            spotify_user_id=spotify_user_id,
            display_name=user_info['display_name'],
        )
        db_session.add(user)
        db_session.commit()
        account_id = user.spotify_user_id  # Fetch the newly created accountId
    
    # Store token and user ID in session
    session['token_info'] = token_info
    session['user_id'] = spotify_user_id
    session['account_id'] = account_id
    
    if custom_id: # If the user has a custom_id, store it in the session
        session['custom_id'] = custom_id
        return redirect(f"http://localhost:5173/accounts/{custom_id}")
    else:
        return redirect(f"http://localhost:5173/accounts/{spotify_user_id}")

# Logout route
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(f"http://localhost:5173/")

# TODO: maybe update with user_id and account_id
# Function to get authenticated Spotify client
def get_spotify_client():
    token_info = session.get('token_info', {})
    sp_oauth = SpotifyOAuth(
        client_id=Config.SPOTIPY_CLIENT_ID,
        client_secret=Config.SPOTIPY_CLIENT_SECRET,
        redirect_uri=Config.SPOTIPY_REDIRECT_URI,
        scope=scope
    )
    if not sp_oauth.is_token_expired(token_info):
        sp = spotipy.Spotify(auth=token_info['access_token'])
    else:
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
        sp = spotipy.Spotify(auth=token_info['access_token'])
    return sp
