from flask import Blueprint, render_template, session, redirect, url_for, send_file

from . import main_bp

from app.auth.routes import get_spotify_client
from app.utils.utils import *


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

@main_bp.route('/play_history')
def play_history():
    if 'token_info' not in session:
        return redirect(url_for('auth.login'))

    # TODO: Add played time

    sp = get_spotify_client()
    play_history = get_play_history(sp)
    return render_template('play_history.html', play_history=play_history)


@main_bp.route('/liked_tracks')
def liked_tracks():
    if 'token_info' not in session:
        return redirect(url_for('auth.login'))

    sp = get_spotify_client()
    liked_tracks = get_liked_tracks(sp)
    return render_template('liked_tracks.html', liked_tracks=liked_tracks)

# Doesnt needed
@main_bp.route('/popular_liked_tracks')
def popular_liked_tracks():
    if 'token_info' not in session:
        return redirect(url_for('auth.login'))

    sp = get_spotify_client()
    liked_tracks = get_liked_tracks(sp)
    liked_tracks_sorted = sorted(liked_tracks, key=lambda x: x['popularity'], reverse=True)
    return render_template('popular_liked_tracks.html', liked_tracks=liked_tracks_sorted)

@main_bp.route('/play_intervals')
def play_intervals():
    if 'token_info' not in session:
        return redirect(url_for('auth.login'))

    sp = get_spotify_client()
    play_intervals = get_play_intervals(sp)
    return render_template('play_intervals.html', play_intervals=play_intervals)

