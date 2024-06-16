from flask import Blueprint, render_template, session, redirect, url_for

from . import main_bp

from app.auth.routes import get_spotify_client
from app.utils.utils import get_top_tracks


@main_bp.route('/', methods=['GET', 'POST'])
def index():
    if 'token_info' not in session:
        return render_template('index.html')
    
    sp = get_spotify_client()
    top_tracks = get_top_tracks(sp, limit=5)
    return render_template('index.html', top_tracks=top_tracks)

@main_bp.route('/results')
def results():
    if 'token_info' not in session:
        return redirect(url_for('auth.login'))

    sp = get_spotify_client()
    top_tracks = get_top_tracks(sp)
    return render_template('results.html', top_tracks=top_tracks)
