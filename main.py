import json, os
import pandas as pd
import plotly.express as px

def plot_df(df, x, y, title=None, x_label=None, y_label=None, sort=False):
    fig = px.bar(x=df[x], y=df[y])
    fig.update_layout(bargap=0.01, xaxis_title=x_label, yaxis_title=y_label, title=title)
    if sort:
        fig.update_layout(xaxis={'categoryorder':'total descending'})
    fig.show()

class musicHistory:
    df = pd.DataFrame()
    total_time = 0

    start_date = 0
    end_date = 0

    def __init__(self):
        substring = 'StreamingHistory'
        directory = './MyData/'
        file_paths = []
        dfs = []

        for root, dirs, files in os.walk(directory):
            for file in files:
                if substring in file:
                    file_path = os.path.join(root, file)
                    file_paths.append(file_path)

        for path in file_paths:
            with open(path, encoding="utf8") as f:
                json_data = pd.json_normalize(json.loads( f.read() ))
                dfs.append(json_data)
        self.df = pd.concat(dfs).reset_index()
        
        self.set_dates()
        self.set_total_time()
        return
    
    def set_total_time(self):
        if self.total_time == 0:
            for index, row in self.df.iterrows():
                self.total_time += row['msPlayed']
        return

    def set_dates(self):
        df = self.df.drop(['artistName', 'trackName', 'msPlayed'], axis=1)
        df.sort_values(by=['endTime'])
        df['endTime'] = pd.to_datetime(df['endTime'])
        df['endTime'] = pd.to_datetime(df['endTime'].dt.strftime("%Y-%m-%d"))
        self.start_date = df.head(1)['endTime'].dt.year.tolist()[0]
        self.end_date = df.tail(1)['endTime'].dt.year.tolist()[0]
        return 

    def load_over_time(self):
        self.df['endTime'] = pd.to_datetime(self.df['endTime'])
        self.df['endTime'] = pd.to_datetime(self.df['endTime'].dt.strftime("%Y-%m-%d"))

        df_time = self.df[['endTime', 'msPlayed']]
        df_time_sum = df_time.groupby(['endTime'], as_index=False).agg({'msPlayed': 'sum'})
        df_time_sum['hrPlayed'] = df_time_sum['msPlayed'] / (1000*60*60)

        plot_df(df_time_sum, 'endTime', 'hrPlayed', title=f"Listening time to Spotify streams per day: {self.start_date}/{self.end_date}", y_label='Hours [h]' )

        return df_time_sum

    def toptracks(self, top=50):
        df_top = self.df.groupby(['trackName', 'artistName'], as_index=False) \
                     .agg({'endTime':'count', 'msPlayed':'sum'}) \
                     .rename(columns={'endTime':'noStreams', 'msPlayed':'streamTimeMs'})
        df_top['streamTimeHr'] = df_top['streamTimeMs']/(1000*60*60)
        df_top = df_top.sort_values(by=['noStreams'], ascending=False)
        df_top = df_top.head(top)
        df_top['fullName'] = df_top['artistName'] + ' - ' + df_top['trackName']

        df_top = df_top.drop(['artistName'], axis=1)
        df_top = df_top.drop(['trackName'], axis=1)
        df_top = df_top.drop(['streamTimeMs'], axis=1)
        
        plot_df(df_top, 'fullName', 'streamTimeHr', title=f"Listening time to Spotify streams by track: {self.start_date}/{self.end_date}", x_label='Track name', y_label='Stream time[Hr]', sort=True)
        plot_df(df_top, 'fullName', 'noStreams', title=f"Number of streams by track: {self.start_date}/{self.end_date}", x_label='Track name', y_label='Number of streams', sort=True)

        return df_top

if __name__ == "__main__":
    history = musicHistory()
    df = history.df

    # Общее время прослушивания 
    total_time = history.total_time
    print(f"Total duration: {(total_time / (1000 * 60))          :.2f} minutes")
    print(f"Total duration: {(total_time / (1000 * 60 * 60))     :.2f} hours")
    print(f"Total duration: {(total_time / (1000 * 60 * 60 * 24)):.2f} days")

    # Время прослушивания по дням
    history.load_over_time()

    # Топ треков: Кол-во прослушиваний треков | Время прослушивания
    history.toptracks(top=20)
