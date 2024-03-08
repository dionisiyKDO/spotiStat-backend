from musicHistory_extended import *
from musicHistory import *
from settings import *

from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

history = MusicHistoryExtendedFile()

@app.context_processor
def inject_colors():
    return dict(colors=spotify_colors)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/data')
def data():
    data = {}
    total_time = history.total_time
    data['total_minutes'] = [ 'Total minutes', total_time / (1000 * 60)]
    data['total_hours'] =   [ 'Total hours', total_time / (1000 * 60 * 60)]
    data['total_days'] =    [ 'Total days', total_time / (1000 * 60 * 60 * 24)]

    return render_template('data.html', data=data)

# region
@app.route('/daily_listening_time')
def daily_listening_time():
    fig = history.daily_listening_time(year=2021, groupByMonth=False)
    plotly_html = fig.to_html(full_html=False)
    return render_template('plot.html', plotly_html=plotly_html)

@app.route('/top_tracks_duration')
def top_tracks_duration():
    fig = history.top_tracks_by_stream_time(year=2023)
    plotly_html = fig.to_html(full_html=False)
    
    return render_template('plot.html', plotly_html=plotly_html)

@app.route('/top_tracks_count')
def top_tracks_count():
    fig = history.top_tracks_by_streams(year=2023)
    plotly_html = fig.to_html(full_html=False)
    
    return render_template('plot.html', plotly_html=plotly_html)
# endregion


if __name__ == "__main__":
    app.run(debug=True)
    # YearlyStats()
    # OverallStats()
