from MusicHistoryExtendedFile import *
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

@app.route('/top_tracks_list')
def top_tracks_list():
    column = request.args.get('column')
    tracks = history.get_top_tracks_data()

    # Check if the column is valid
    if column in tracks.columns:
        # Sort the DataFrame based on the selected column
        tracks_sorted = tracks.sort_values(by=column, ascending=False)
        return render_template('top_tracks_list.html', tracks=tracks_sorted.head(50))
    else:
        tracks_sorted = tracks.sort_values(by=['streamTimeHr'], ascending=False)
        return render_template('top_tracks_list.html', tracks=tracks_sorted.head(50))

@app.route('/top_tracks_list/sort')
def sort():
    column = request.args.get('column')

    tracks = history.get_top_tracks_data()
    tracks = tracks.sort_values(by=['streamTimeHr'], ascending=False)
    
    # Check if the column is valid
    if column in tracks.columns:
        # Sort the DataFrame based on the selected column
        tracks_sorted = tracks.sort_values(by=column, ascending=False)
        return render_template('index.html', tracks=tracks_sorted)
    else:
        # If column is not valid, render the template with unsorted DataFrame
        return render_template('index.html', tracks=tracks)

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
