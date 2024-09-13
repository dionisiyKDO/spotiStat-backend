from flask import Blueprint, redirect, request, session, url_for, jsonify
from app.config import Config
import spotipy
from spotipy.oauth2 import SpotifyOAuth

auth_bp = Blueprint('auth', __name__)

# Check session status route
@auth_bp.route('/auth/session')
def session_status():
    token_info = session.get('token_info', None)
    logged_in = token_info is not None
    return jsonify({'logged_in': logged_in})

# Route for initiating Spotify login
@auth_bp.route('/auth/login')
def login():
    sp_oauth = SpotifyOAuth(
        client_id=Config.SPOTIPY_CLIENT_ID,
        client_secret=Config.SPOTIPY_CLIENT_SECRET,
        redirect_uri=Config.SPOTIPY_REDIRECT_URI,
        scope="user-library-read user-read-recently-played user-top-read"
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
        scope="user-library-read user-read-recently-played user-top-read"
    )
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(f"http://localhost:5173/")

# Logout route
@auth_bp.route('/auth/logout')
def logout():
    session.clear()
    return redirect(f"http://localhost:5173/")

# Function to get authenticated Spotify client
def get_spotify_client():
    token_info = session.get('token_info', {})
    sp_oauth = SpotifyOAuth(
        client_id=Config.SPOTIPY_CLIENT_ID,
        client_secret=Config.SPOTIPY_CLIENT_SECRET,
        redirect_uri=Config.SPOTIPY_REDIRECT_URI,
        scope="user-library-read user-read-recently-played user-top-read"
    )
    if not sp_oauth.is_token_expired(token_info):
        sp = spotipy.Spotify(auth=token_info['access_token'])
    else:
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
        sp = spotipy.Spotify(auth=token_info['access_token'])
    return sp