import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template, request
import os

# Use environment variables for credentials
CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI', 'http://127.0.0.1:8000/callback')

# Create a Spotify OAuth object
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope='user-library-read'))

app = Flask(__name__)


def get_artists_in_genre_and_year_range(genre, start_year, end_year, offsets):
    artists = set()

    # Iterate over the years in the specified range
    for year in range(start_year, end_year + 1):
        # Iterate over the offsets
        for offset in offsets:
            try:
                # Search for artists with tracks released in the specified year
                results = sp.search(q=f'genre:{genre} year:{year}', type='artist', limit=50, offset=offset)

                # Extract artists from the search results
                for artist in results['artists']['items']:
                    artists.add(artist['name'])
            except Exception as e:
                print(f"Error searching for year {year}, offset {offset}: {e}")
                continue

    return list(artists)


def get_artist_info(artist_name):
    try:
        # Search for the artist
        results = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
        
        if not results['artists']['items']:
            return None
            
        artist = results['artists']['items'][0]

        # Get the artist ID, images, popularity, and genres
        artist_id = artist['id']
        images = artist['images'][0]['url'] if artist['images'] else None
        popularity = artist['popularity']
        genres = artist['genres']

        # Get the number of albums
        albums = sp.artist_albums(artist_id, album_type='album', limit=1)
        num_albums = albums['total']

        return {
            'Artist': artist_name,
            'Artist ID': artist_id,
            'Images': images,
            'Popularity': popularity,
            'Number of Albums': num_albums,
            'Genres': genres
        }
    except Exception as e:
        print(f"Error getting info for {artist_name}: {e}")
        return None


def create_artists_dataframe(artists_list):
    # Use ThreadPoolExecutor to parallelize API calls
    with ThreadPoolExecutor() as executor:
        artist_data = list(executor.map(get_artist_info, artists_list))
        # Filter out None values
        artist_data = [data for data in artist_data if data is not None]
        df = pd.DataFrame(artist_data)

    return df


@app.route('/callback', methods=['GET'])
def callback():
    code = request.args.get('code')
    return 'Callback received successfully!'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Get user input from the form
            desired_genre = request.form['genre']
            start1_year = request.form['start_year']
            end1_year = request.form['end_year']
            offsets_str = request.form['offsets']

            # Convert inputs to appropriate types
            desired_start_year = int(start1_year)
            desired_end_year = int(end1_year)
            desired_offsets = [int(offset) for offset in offsets_str.split(",")]

            # Get the list of artists in the specified genre and year range
            artists_list = get_artists_in_genre_and_year_range(desired_genre, desired_start_year, desired_end_year, desired_offsets)

            if not artists_list:
                return render_template('index.html', error="No artists found for the given criteria.")

            # Create the artists DataFrame
            artists_df = create_artists_dataframe(artists_list)

            if artists_df.empty:
                return render_template('index.html', error="No artist data could be retrieved.")

            # Convert DataFrame to HTML table
            artists_table = artists_df.to_html(classes='table table-striped', index=False)

            return render_template('result.html', table=artists_table)
        
        except Exception as e:
            return render_template('index.html', error=f"An error occurred: {str(e)}")

    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))