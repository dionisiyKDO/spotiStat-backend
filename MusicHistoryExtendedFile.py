import json, os
import pandas as pd
import plotly.express as px

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.mode.chained_assignment = None

class MusicHistoryExtendedFile:
    def __init__(self, path='./MyData_all/'):
        self.df = pd.DataFrame()
        self.total_time = 0
        self.start_year = 0
        self.end_year = 0
        self.__load_data(path)
        self.__set_total_time()
        self.__set_dates()

    def __load_data(self, path):
        substring = 'Streaming'
        file_paths = []

        # get paths to files with our data
        for root, dirs, files in os.walk(path):
            for file in files:
                if substring in file:
                    file_path = os.path.join(root, file)
                    file_paths.append(file_path)

        # read these files and unite them into one DataFrame
        dfs = [pd.json_normalize(json.loads(open(file_path, encoding="utf8").read())) for file_path in file_paths]
        self.df = pd.concat(dfs).reset_index()

    def __set_total_time(self):
        """Calculate total streaming time, save it to class variable"""
        if self.total_time == 0:
            for index, row in self.df.iterrows():
                self.total_time += row['ms_played']
        return

    def __set_dates(self):
        """Get start_year and end_year, save it to class variables"""
        df_copy = self.df[['ts']].copy()
        df_copy['ts'] = pd.to_datetime(df_copy['ts']).dt.date
        self.start_year = df_copy['ts'].min().year
        self.end_year = df_copy['ts'].max().year
        return 

    def get_top_tracks_data(self, year=None):
        df_top = self.df[['spotify_track_uri', 'ts', 'master_metadata_track_name', 'master_metadata_album_artist_name', 'ms_played']].copy()
        df_top['ts'] = pd.to_datetime(df_top['ts'])
        if year: df_top = df_top[df_top['ts'].dt.year == year]
        print(df_top.columns)
        df_top['fullName'] = df_top['master_metadata_album_artist_name'] + ' - ' + df_top['master_metadata_track_name']
        print(df_top.columns)
        df_top = df_top.groupby(['spotify_track_uri', 'fullName', 'master_metadata_track_name', 'master_metadata_album_artist_name'], as_index=False)
        df_top = df_top.agg({'ts':'count', 'ms_played':'sum'})
        df_top = df_top.rename(columns={'ts': 'noStreams', 'ms_played': 'streamTimeMs'})
        df_top['streamTimeHr'] = df_top['streamTimeMs'] / (1000 * 60 * 60)
        return df_top
    
    def top_tracks_by_stream_time(self, top=None, threshold_time_hrs=1, year=None):
        """Top tracks by streaming time"""
        df_top = self.get_top_tracks_data(year=year)
        df_top = df_top[df_top['streamTimeHr'] > threshold_time_hrs] if threshold_time_hrs else df_top
        df_top = df_top.sort_values(by=['streamTimeHr'], ascending=False)
        title = f"Top tracks by streaming time: {year}" if year else f"Top tracks by streaming time: {self.start_year}/{self.end_year}"
        return self.__generate_bar_plot(df_top, x='fullName', y='streamTimeHr', title=title, xaxis_title='Track name', yaxis_title='Streaming time [hours]')

    def top_tracks_by_streams(self, top=None, threshold_number=10, year=None):
        """Top tracks by number of streams"""
        df_top = self.get_top_tracks_data(year=year)
        df_top = df_top[df_top['noStreams'] > threshold_number] if threshold_number else df_top
        df_top = df_top.sort_values(by=['noStreams'], ascending=False)
        title = f"Top tracks by number of streams: {year}" if year else f"Top tracks by number of streams: {self.start_year}/{self.end_year}"
        return self.__generate_bar_plot(df_top, x='fullName', y='noStreams', title=title, xaxis_title='Track name', yaxis_title='Number of streams')

    def daily_listening_time(self, year: int = None, groupByMonth: bool = None):
        """
        Daily listening time graph.

        This method generates graph visualizing daily listening time of Spotify.

        Parameters
        ----------
        year : int, optional
            Whether to select data for a specific year.
        groupByMonth : bool, optional
            Whether to aggregated data by months.
        """
        # copy df with only ts and ms_played columns, change ts to format with only date
        df_time = self.df[['ts', 'ms_played']].copy()
        df_time['ts'] = pd.to_datetime(df_time['ts'])
        
        # group by month, or by days
        if groupByMonth:
            df_time['ts'] = pd.to_datetime(df_time['ts'].dt.strftime("%Y-%m"))
        else:
            df_time['ts'] = pd.to_datetime(df_time['ts'].dt.strftime("%Y-%m-%d"))
        
        # group records by date, summing listening time. Change miliseconds to hours
        df_time_sum = df_time.groupby(['ts'], as_index=False).agg({'ms_played': 'sum'})
        df_time_sum['hrPlayed'] = df_time_sum['ms_played'] / (1000*60*60)

        # select specific year
        if year:
            df_time_sum = df_time_sum[df_time_sum['ts'].dt.year == year]
            title = f"Listening time to Spotify streams per day: {year}"
        else:
            title = f"Listening time to Spotify streams per day: {self.start_year}/{self.end_year}"
        
        fig = self.__generate_bar_plot(df_time_sum, x='ts', y='hrPlayed', title=title, xaxis_title='', yaxis_title='Hours [h]')
        fig.update_traces(hovertemplate='<b>Date:</b> %{x|%d %b %Y}<br><b>Streaming time:</b> %{y}<br>')
        return fig
    
    @staticmethod
    def __generate_bar_plot(data, x, y, title, xaxis_title, yaxis_title):
        fig = px.bar(data, x=x, y=y, labels={x: xaxis_title, y: yaxis_title}, title=title)
        fig.update_layout(bargap=0.05)
        return fig
    
