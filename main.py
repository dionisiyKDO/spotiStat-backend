from musicHistory_extended import *
from musicHistory import *

from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

history = musicHistory_extended_file()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/plot')
def plot():
    fig = history.daily_listening_time(year=2021, groupByMonth=False)
    plotly_html = fig.to_html(full_html=False)
    return render_template('plot.html', plotly_html=plotly_html)


def YearlyStats():
    history = musicHistory()

    # Общее время прослушивания 
    total_time = history.total_time
    print(f"Total duration: {(total_time / (1000 * 60))          :.2f} minutes")
    print(f"Total duration: {(total_time / (1000 * 60 * 60))     :.2f} hours")
    print(f"Total duration: {(total_time / (1000 * 60 * 60 * 24)):.2f} days")

    # Время прослушивания по дням
    history.load_over_time()

    # Топ треков: Кол-во прослушиваний треков | Время прослушивания
    history.toptracks(top=20)

def OverallStats():
    # Общее время прослушивания 
    total_time = history.total_time
    print(f"Total duration: {(total_time / (1000 * 60))          :.2f} minutes")
    print(f"Total duration: {(total_time / (1000 * 60 * 60))     :.2f} hours")
    print(f"Total duration: {(total_time / (1000 * 60 * 60 * 24)):.2f} days")

    # Время прослушивания по дням
    history.daily_listening_time(year=2021, groupByMonth=False)

    # Топ треков: Кол-во прослушиваний треков | Время прослушивания
    history.top_tracks(top=None, 
                       threshold_number=10,
                       noStreamsGrph=True, 
                       threshold_time_hrs=1,
                       streamTimeGrph=True,
                       year=2023)


if __name__ == "__main__":
    app.run(debug=True)
    # YearlyStats()
    # OverallStats()
