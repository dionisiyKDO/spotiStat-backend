import json, os
import pandas as pd
import plotly.express as px

class musicHistory_extended_file:
    df = pd.DataFrame()
    total_time = 0
    start_year = 0
    end_year = 0

    def __init__(self, path: str='./MyData_all/'):
        substring = 'Streaming'
        file_paths = []
        dfs = []

        # get paths to files with our data
        for root, dirs, files in os.walk(path):
            for file in files:
                if substring in file:
                    file_path = os.path.join(root, file)
                    file_paths.append(file_path)

        # read this files and unite them to one DataFrame
        for path in file_paths:
            with open(path, encoding="utf8") as f:
                json_data = pd.json_normalize(json.loads( f.read() ))
                dfs.append(json_data)
        self.df = pd.concat(dfs).reset_index()
        
        self.__set_dates()
        self.__set_total_time()
        return
    
    def __set_total_time(self):
        """Calculate total streaming time, save it to class variable"""
        if self.total_time == 0:
            for index, row in self.df.iterrows():
                self.total_time += row['ms_played']
        return

    def __set_dates(self):
        """Get start_date and end_date, save it to class variables"""
        # drop every column, except 'ts'
        df_copy = self.df.drop(['username', 'platform', 'ms_played', 'conn_country', 
            'ip_addr_decrypted', 'user_agent_decrypted', 'master_metadata_track_name', 
            'master_metadata_album_artist_name', 'master_metadata_album_album_name', 
            'spotify_track_uri', 'episode_name', 'episode_show_name', 'spotify_episode_uri', 
            'reason_start', 'reason_end', 'shuffle', 'skipped', 'offline', 'offline_timestamp', 
            'incognito_mode'], axis=1)
    
        # sort by timestamp(ts), get start_year end_year, save it
        df_copy.sort_values(by=['ts'])
        df_copy['ts'] = pd.to_datetime(df_copy['ts'])
        df_copy['ts'] = pd.to_datetime(df_copy['ts'].dt.strftime("%Y-%m-%d"))
        self.start_year = df_copy.head(1)['ts'].dt.year.tolist()[0]
        self.end_year = df_copy.tail(1)['ts'].dt.year.tolist()[0]
        return 

    def daily_listening_time(self, year=None, groupByMonth=None):
        """Daily listening time graph"""
        # copy df with only ts and ms_played columns, change ts to format with only date
        df_time = self.df[['ts', 'ms_played']]
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
        
        # plot Daily listening time graph
        fig = px.bar(df_time_sum, 
                     x='ts', y='hrPlayed', 
                     title=title)
        fig.update_traces(hovertemplate='<b>Date:</b> %{x|%b %Y}<br><b>Streaming time:</b> %{y}<br>')
        fig.update_layout(bargap=0.05, yaxis_title='Hours [h]', xaxis_title=None)
        # fig.show()
        return fig

    def top_tracks(self, top=None, noStreamsGrph=True, streamTimeGrph=False, threshold_number=10, threshold_time_hrs=1, year=None):
        """Top tracks graph by number of streams/stream time"""
        # Group records by track name and artist, summing listening time and counting number of streams. Change miliseconds to hours
        df_top = self.df
        df_top['ts'] = pd.to_datetime(df_top['ts'])
        fig = None

        if year:
            df_top = df_top[df_top['ts'].dt.year == year]
        if noStreamsGrph or streamTimeGrph:
            df_top = df_top.groupby(['master_metadata_track_name', 'master_metadata_album_artist_name'], as_index=False) \
                        .agg({'ts':'count', 'ms_played':'sum'}) \
                        .rename(columns={'ts':'noStreams', 'ms_played':'streamTimeMs'})
            df_top['fullName'] = df_top['master_metadata_album_artist_name'] + ' - ' + df_top['master_metadata_track_name']
            df_top['streamTimeHr'] = df_top['streamTimeMs']/(1000*60*60)
            df_top = df_top.drop(['master_metadata_album_artist_name'], axis=1)
            df_top = df_top.drop(['master_metadata_track_name'], axis=1)
            df_top = df_top.drop(['streamTimeMs'], axis=1)
        
        # Number of streams by track + Streaming time
        if noStreamsGrph:
            df_top_noStreams = df_top.sort_values(by=['noStreams'], ascending=False)
            if top:
                df_top_noStreams = df_top_noStreams.head(top)
            if threshold_number:
                df_top_noStreams = df_top_noStreams[df_top_noStreams['noStreams'] > threshold_number] 
            if year:
                title = f"Number of streams by track: {year} ||| Number of tracks: {df_top_noStreams.shape[0]}"
            else:
                title = f"Number of streams by track: {self.start_year}/{self.end_year} ||| Number of tracks: {df_top_noStreams.shape[0]}"
            fig = px.bar(df_top_noStreams, 
                         x='fullName', y='noStreams', 
                         labels={'Column1' : 'Track name', 'Column2' : 'Number of streams'},
                         hover_data={'streamTimeHr': ':.2f'},
                         title=title)
            fig.update_traces(hovertemplate='<b>Track: </b>%{x}<br><b>Number of Streams: </b>%{y}<br><b>Stream Time (hours): </b>%{customdata[0]:.2f}')
            fig.update_layout(bargap=0.01)
            # fig.show()

        # Streaming time by track + Number of streams
        if streamTimeGrph:
            df_top_streamTimeHr = df_top.sort_values(by=['streamTimeHr'], ascending=False)
            if top:
                df_top_streamTimeHr = df_top_streamTimeHr.head(top)
            if threshold_time_hrs:
                df_top_streamTimeHr = df_top_streamTimeHr[df_top_streamTimeHr['streamTimeHr'] > threshold_time_hrs] 
            if year:
                title = f"Streaming time by track: {year} ||| Number of tracks: {df_top_streamTimeHr.shape[0]}"
            else:
                title = f"Streaming time by track: {self.start_year}/{self.end_year} ||| Number of tracks: {df_top_streamTimeHr.shape[0]}"
            
            fig = px.bar(df_top_streamTimeHr, 
                         x='fullName', y='streamTimeHr', 
                         labels={'Column1' : 'Track name', 'Column2' : 'Streaming time'},
                         hover_data={'noStreams': ':.0f'},
                         title=title)
            fig.update_traces(hovertemplate='<b>Track: </b>%{x}<br><b>Stream Time (hours): </b>%{y:.2f}<br><b>Number of Streams: </b>%{customdata[0]}')
            fig.update_layout(bargap=0.01)
            # fig.show()
        
        return fig
