# Author: Jacob Madsen
# Feb. 2021
# Script to find movies and their corresponding soundtracks from IMDb,
# and then record the audio features of the soundtracks via the Spotify API.

import requests
from imdb import IMDb, IMDbError
import random
import logging
import csv

ia = IMDb()

# disabling logger to prevent 404's from breaking program
logger = logging.getLogger('imdbpy')
logger.disabled = True

# To obtain a client ID and secret, navigate to your
# dashboard at https://developer.spotify.com/
#########################################################
#CLIENT_ID =  <put your client ID here> #
#CLIENT_SECRET =  <put your client secret here> #
#########################################################

AUTH_URL = 'https://accounts.spotify.com/api/token'
auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
})

# convert the response to JSON
auth_response_data = auth_response.json()

# save the access token
access_token = auth_response_data['access_token']

headers = {
    'Authorization': 'Bearer {token}'.format(token=access_token)
}
BASE_URL = 'https://api.spotify.com/v1/'

# .csv file to record data collected
movie_file = open('movie_data.csv', mode='w')
movie_file.write('Title,Genre_1,Genre_2,Genre_3,Num_Tracks,Avg_Valence,Avg_Danceability,Avg_Energy,Avg_Key,Avg_Loudness,Avg_Mode,Avg_Speechiness,Avg_Acousticness,Avg_Instrumentallness,Avg_Liveness,Avg_Tempo\n')

num_invalid_movies = 0
num_data_points = 0
num_rich_data_points = 0
while(num_data_points < 500):

    has_soundtrack_info = True
    has_genre_info = True
    soundtracks = []
    genres = []

    # audio features
    num_audio_features = 0
    total_valence = 0.0
    total_danceability = 0.0
    total_energy = 0.0
    total_key = 0.0
    total_loudness = 0.0
    total_mode = 0.0
    total_speechiness = 0.0
    total_acousticness = 0.0
    total_instrumentalness = 0.0
    total_liveness = 0.0
    total_tempo = 0.0

    # Movie ID for "The Matrix" : 0133093

    # get a movie
    valid_movie = False
    while(not valid_movie):
        ranInt = random.randint(0, 100000)
        try:
            movie = ia.get_movie(100000 + ranInt)
            valid_movie = True
        except:
            num_invalid_movies += 1
            valid_movie = False
        if(not 'title' in movie.keys()):
            num_invalid_movies += 1
            valid_movie = False

    # title
    title = str(movie['title'])

    # soundtracks
    ia.update(movie, 'soundtrack')
    if('soundtrack' in movie.keys()):
        for i in range(len(movie['soundtrack'])):
            track_name = list(movie['soundtrack'][i].keys())[0]
            if(track_name == 'It looks like we don\'t have any Soundtracks for this title yet.'):
                has_soundtrack_info = False
                break
            if(has_soundtrack_info):
                artist = 'N/A'
                if('performed by' in list(movie['soundtrack'][i][track_name].keys())):
                    artist = movie['soundtrack'][i][track_name]['performed by']
                    soundtracks.append((track_name, artist))
        if(has_soundtrack_info):
            # genres
            if('genres' in list(movie.keys())):
                for i in range(len(movie['genres'])):
                    genres.append(str(movie['genres'][i]))
            else:
                has_genre_info = False
    else:
        num_invalid_movies += 1

    # I chose to only get soundtrack info for movies that had genre info
    if(has_genre_info and has_soundtrack_info):

        # Getting spotify track IDs of soundtracks
        for k in range(len(soundtracks)):
            resp = requests.get(BASE_URL + 'search?q=track:' + soundtracks[k][0].replace(' ', '%20')
                                + 'artist:' + soundtracks[k][1].replace(' ', '%20') + '&type=track&limit=1', headers=headers)
            print(str(resp.status_code) + ' | ', end='')
            data = resp.json()
            if('tracks' in data.keys()):
                if(len(data['tracks']['items']) > 0):

                    # track is on Spotify... getting audio features of the track
                    # Note: The Spotify API has "Get audio features of several tracks" which I do not use. This could
                    #       definitely be used instead to reduce the number of requests.
                    num_audio_features += 1
                    track_ID = data['tracks']['items'][0]['id']
                    resp2 = requests.get(
                        BASE_URL + 'audio-features/' + track_ID, headers=headers)
                    print(str(resp2.status_code) + ' : ', end='')
                    audio_features = resp2.json()
                    total_danceability += audio_features['danceability']
                    total_energy += audio_features['energy']
                    total_key += audio_features['key']
                    total_loudness += audio_features['loudness']
                    total_mode += audio_features['mode']
                    total_speechiness += audio_features['speechiness']
                    total_acousticness += audio_features['acousticness']
                    total_instrumentalness += audio_features['instrumentalness']
                    total_liveness += audio_features['liveness']
                    total_valence += audio_features['valence']
                    total_tempo += audio_features['tempo']

        # Printing and recording data points with genre info and
        # at least one soundtrack with spotify audio features
        if(num_audio_features > 0):
            num_data_points += 1
            if(num_audio_features >= 3):
                num_rich_data_points += 1

            # well-formatted printing of the data gathered
            print(
                '\n----------------------------------------------------------------------------------------------------------')
            print('Title: ' + title)
            print('Genres: ' + str(genres))

            print('Number of Soundtracks: ' + str(num_audio_features))
            print('Average Valence: ' + str(total_valence/num_audio_features))
            print('Average Danceability: ' +
                  str(total_danceability/num_audio_features))
            print('Average Energy: ' + str(total_energy/num_audio_features))
            print('Average Key: ' + str(total_key/num_audio_features))
            print('Average Loudness: ' +
                  str(total_loudness/num_audio_features))
            print('Average Mode: ' + str(total_mode/num_audio_features))
            print('Average Speechiness: ' +
                  str(total_speechiness/num_audio_features))
            print('Average Acousticness: ' +
                  str(total_acousticness/num_audio_features))
            print('Average Instrumentalness: ' +
                  str(total_instrumentalness/num_audio_features))
            print('Average Liveness: ' +
                  str(total_liveness/num_audio_features))
            print('Average Tempo: ' + str(total_tempo/num_audio_features))

            print('\nNumber of Invalid Movies: ' + str(num_invalid_movies))
            print('Number of Data Points: ' + str(num_data_points))
            print('Number of Data Points w/ 3+ Tracks: ' +
                  str(num_rich_data_points))

            # writing to .csv file
            # Note: Movies with titles containing commas will cause a slight error in the .csv file.
            #       Since this happens so infrequently and is easy to fix after the fact, I didn't bother to fix it here.
            if(len(genres) == 1):
                movie_file.write(title + ',' + genres[0] + ',N/A,N/A,' + str(num_audio_features) + ',' + str(total_valence/num_audio_features) + ',' + str(total_danceability/num_audio_features) + ',' + str(total_energy/num_audio_features) + ',' + str(total_key/num_audio_features) + ',' + str(
                    total_loudness/num_audio_features) + ',' + str(total_mode/num_audio_features) + ',' + str(total_speechiness/num_audio_features) + ',' + str(total_acousticness/num_audio_features) + ',' + str(total_instrumentalness/num_audio_features) + ',' + str(total_liveness/num_audio_features) + ',' + str(total_tempo/num_audio_features) + '\n')
            elif(len(genres) == 2):
                movie_file.write(title + ',' + genres[0] + ',' + genres[1] + ',N/A,' + str(num_audio_features) + ',' + str(total_valence/num_audio_features) + ',' + str(total_danceability/num_audio_features) + ',' + str(total_energy/num_audio_features) + ',' + str(total_key/num_audio_features) + ',' + str(
                    total_loudness/num_audio_features) + ',' + str(total_mode/num_audio_features) + ',' + str(total_speechiness/num_audio_features) + ',' + str(total_acousticness/num_audio_features) + ',' + str(total_instrumentalness/num_audio_features) + ',' + str(total_liveness/num_audio_features) + ',' + str(total_tempo/num_audio_features) + '\n')
            else:
                movie_file.write(title + ',' + genres[0] + ',' + genres[1] + ',' + genres[2] + ',' + str(num_audio_features) + ',' + str(total_valence/num_audio_features) + ',' + str(total_danceability/num_audio_features) + ',' + str(total_energy/num_audio_features) + ',' + str(total_key/num_audio_features) + ',' + str(
                    total_loudness/num_audio_features) + ',' + str(total_mode/num_audio_features) + ',' + str(total_speechiness/num_audio_features) + ',' + str(total_acousticness/num_audio_features) + ',' + str(total_instrumentalness/num_audio_features) + ',' + str(total_liveness/num_audio_features) + ',' + str(total_tempo/num_audio_features) + '\n')
    else:
        num_invalid_movies += 1

movie_file.close()
