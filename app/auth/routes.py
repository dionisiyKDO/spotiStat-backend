from flask import Blueprint, redirect, request, session, url_for

from . import auth_bp
from app.config import Config

import spotipy
from spotipy.oauth2 import SpotifyOAuth

@auth_bp.route('/login')
def login():
    sp_oauth = SpotifyOAuth(
        client_id=Config.SPOTIPY_CLIENT_ID,
        client_secret=Config.SPOTIPY_CLIENT_SECRET,
        redirect_uri=Config.SPOTIPY_REDIRECT_URI,
        scope="user-library-read user-read-recently-played user-top-read"
    )
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

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
    return redirect(url_for('main.index'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

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