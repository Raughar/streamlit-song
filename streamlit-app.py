# Importing the libraries
import streamlit as st
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings
import spotipy
import requests
from bs4 import BeautifulSoup
from spotipy.oauth2 import SpotifyClientCredentials
import os
import dotenv
warnings.filterwarnings("ignore")

#Function to get the Billboard Hot 100 songs
def get_billboard_top():
    r = requests.get('https://www.billboard.com/charts/hot-100/').content
    soup = BeautifulSoup(r, 'html.parser')
    n1_song = soup.find_all('h3', attrs={'class': 'c-title a-no-trucate a-font-primary-bold-s u-letter-spacing-0021 u-font-size-23@tablet lrv-u-font-size-16 u-line-height-125 u-line-height-normal@mobile-max a-truncate-ellipsis u-max-width-245 u-max-width-230@tablet-only u-letter-spacing-0028@tablet'})
    songs = soup.find_all('h3', attrs={'class': 'c-title a-no-trucate a-font-primary-bold-s u-letter-spacing-0021 lrv-u-font-size-18@tablet lrv-u-font-size-16 u-line-height-125 u-line-height-normal@mobile-max a-truncate-ellipsis u-max-width-330 u-max-width-230@tablet-only'})
    n1_artist = soup.find_all('span', attrs={'class': 'c-label a-no-trucate a-font-primary-s lrv-u-font-size-14@mobile-max u-line-height-normal@mobile-max u-letter-spacing-0021 lrv-u-display-block a-truncate-ellipsis-2line u-max-width-330 u-max-width-230@tablet-only u-font-size-20@tablet'})
    artists = soup.find_all('span', attrs={'class': 'c-label a-no-trucate a-font-primary-s lrv-u-font-size-14@mobile-max u-line-height-normal@mobile-max u-letter-spacing-0021 lrv-u-display-block a-truncate-ellipsis-2line u-max-width-330 u-max-width-230@tablet-only'})
    df = pd.DataFrame({
        "Song": [song.text for song in songs],
        "Artist": [artist.text for artist in artists]
    })
    df.loc[0] = [n1_song[0].text, n1_artist[0].text]
    df['Song'] = df['Song'].str.replace('\n', '').str.replace('\t', '')
    df['Artist'] = df['Artist'].str.replace('\n', '').str.replace('\t', '')
    return df

#Function to get the song features
def get_song_features(track_id):
    track = sp.track(track_id)
    features = sp.audio_features(track_id)
    song = {
        'explicit': track['explicit'],
        'danceability': features[0]['danceability'],
        'energy': features[0]['energy'],
        'key': features[0]['key'],
        'loudness': features[0]['loudness'],
        'mode': features[0]['mode'],
        'speechiness': features[0]['speechiness'],
        'acousticness': features[0]['acousticness'],
        'instrumentalness': features[0]['instrumentalness'],
        'liveness': features[0]['liveness'],
        'valence': features[0]['valence'],
        'tempo': features[0]['tempo'],
        'duration_ms': features[0]['duration_ms'],
        'time_signature': features[0]['time_signature'],
        'year': track['album']['release_date'][:4],
        'track_id': track_id,
        'name': track['name'],
        'artist': track['artists'][0]['name'],
    }
    return [song]

#Function to get the most popular song of the artist
def get_popular_song(artist):
    results = sp.search(q=artist, limit=1)
    artist_id = results['tracks']['items'][0]['artists'][0]['id']
    top_tracks = sp.artist_top_tracks(artist_id)
    return top_tracks['tracks'][0]['id']

#Initialize the Spotify API
client_id = st.secrets['CLIENT_ID']
client_secret = st.secrets['CLIENT_SECRET']
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

#Creating a cache for the big dataset
@st.cache
def get_data():
    data = pd.read_csv(f'https://dl.dropboxusercontent.com/scl/fi/zc5e1lnzzjw7knzh58vgy/tracks_features.csv?rlkey=6lkmcs1z9ik6gjyj92blk9bw4v')
    return data

#Reading the data
features = get_data()
billboard = get_billboard_top()

# Running KMeans
kmeans = KMeans(n_clusters=15, init='k-means++', max_iter=300, n_init=10, random_state=0)
kmeans.fit(scaled_features)

# Saving the clusters in a new variable
cluster = kmeans.predict(scaled_features)

# Uniting the clusters with the features and song information
clustered_features = pd.DataFrame(scaled_features, columns=features.drop(['name', 'artists', 'album'], axis=1).columns)
clustered_features['name'] = features['name']
clustered_features['artists'] = features['artists']
clustered_features['album'] = features['album']
clustered_features['cluster'] = cluster

# Streamlit code
st.title('Song Recommender')
st.write('This is a simple song recommender app.')

# Display the Billboard Hot 100 songs
st.subheader('Billboard Hot 100 Songs')
st.dataframe(billboard)

# Add a selectbox for the user to choose whether they want to search by song or artist
select = st.selectbox('Do you want to search by song or artist?', ('song', 'artist'))

# If the user selects song, we will ask for the name of the song
if select == 'song':
    song = st.text_input('Enter the name of a song')
    if song:
        # Checking if the song is in the Billboard Hot 100
        if song in list(billboard['Song']):
            filtered_billboard = billboard[billboard['Song'] != song]
            random_song = filtered_billboard.sample()
            st.write(f'We recommend the song {random_song["Song"].values[0]} by {random_song["Artist"].values[0]}')
        else:
            st.write('The song is not in the Billboard Hot 100')
            if st.button('Would you like a random song that is not in the Billboard Hot 100?'):
                if song in list(features['name']):
                    song_index = features[features['name'] == song].index[0]
                    song_features = selected_features.iloc[song_index]
                    song_features = scaler.transform([song_features])
                    song_cluster = kmeans.predict(song_features)
                    similar_songs = clustered_features[clustered_features['cluster'] == song_cluster[0]].sample()
                    print(f'We recommend the song {similar_songs["name"].values[0]} by {similar_songs["artists"].values[0]}')
                else:
                    #Searching for the song in Spotify with the help of Spotipy
                    results = sp.search(q=song, limit=1)

                    #Getting the song features
                    song_id = results['tracks']['items'][0]['id']
                    song_features = get_song_features(song_id)
                    song_features = pd.DataFrame(song_features)
                    song_features = song_features.drop(columns=['track_id', 'name', 'artist'])
                    song_features = scaler.transform(song_features)
                    song_cluster = kmeans.predict(song_features)
                    similar_songs = clustered_features[clustered_features['cluster'] == song_cluster[0]].sample()
                    print(f'We recommend the song {similar_songs["name"].values[0]} by {similar_songs["artists"].values[0]}')

# If the user selects artist, we will ask for the name of the artist
else:
    artist = st.text_input('Enter the name of an artist')
    if artist:
        # Checking if the artist is in the Billboard Hot 100
        if artist in list(billboard['Artist']):
            filtered_billboard = billboard[billboard['Artist'] == artist]
            random_song = filtered_billboard.sample()
            st.write(f'We recommend the song {random_song["Song"].values[0]} by {random_song["Artist"].values[0]}')
        else:
            st.write('The artist is not in the Billboard Hot 100')
            if st.button('Would you like a random song that is not in the Billboard Hot 100?'):
               #Getting the artist's most popular song
                song_id = get_popular_song(artist)
                song_features = get_song_features(song_id)
                song_features = pd.DataFrame(song_features)
                song_features = song_features.drop(columns=['track_id', 'name', 'artist'])
                song_features = scaler.transform(song_features)
                song_cluster = kmeans.predict(song_features)
                similar_songs = clustered_features[clustered_features['cluster'] == song_cluster[0]].sample()
                print(f'We recommend the song {similar_songs["name"].values[0]} by {similar_songs["artists"].values[0]}')