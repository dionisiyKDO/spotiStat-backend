from musicHistory_extended import *
from musicHistory import *

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
    history = musicHistory_extended()

    # Общее время прослушивания 
    # total_time = history.total_time
    # print(f"Total duration: {(total_time / (1000 * 60))          :.2f} minutes")
    # print(f"Total duration: {(total_time / (1000 * 60 * 60))     :.2f} hours")
    # print(f"Total duration: {(total_time / (1000 * 60 * 60 * 24)):.2f} days")

    # Время прослушивания по дням
    # history.daily_listening_time(year=2021, groupByMonth=False)

    # Топ треков: Кол-во прослушиваний треков | Время прослушивания
    history.top_tracks(top=None, 
                       threshold_number=10,
                       noStreamsGrph=True, 
                       threshold_time_hrs=1,
                       streamTimeGrph=True,
                       year=2023)




if __name__ == "__main__":
    # YearlyStats()
    OverallStats()
