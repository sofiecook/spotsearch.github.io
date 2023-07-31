import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template, request

# Replace with your own credentials from the Spotify Developer Dashboard
CLIENT_ID = '5bfb22e08df844f58fd1e84a0f3ae5f7'
CLIENT_SECRET = '281e04f77b564406bfae51c373de325b'
REDIRECT_URI = 'http://127.0.0.1:8000/callback'

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
            # Search for artists with tracks released in the specified year
            results = sp.search(q=f'genre:{genre} year:{year}', type='artist', limit=50, offset=offset)

            # Extract artists from the search results
            for artist in results['artists']['items']:
                artists.add(artist['name'])

    return list(artists)
"""
# Specify your desired genre and year range
desired_genre = input("Genre:")
start1_year = input("Starting year:")
end1_year = input("Ending year:")
offsets_str = input("Enter a comma-separated list of offsets:")

# Convert inputs to appropriate types
desired_start_year = int(start1_year)
desired_end_year = int(end1_year)
desired_offsets = [int(offset) for offset in offsets_str.split(",")]

# Get the list of artists in the specified genre and year range
artists_list = get_artists_in_genre_and_year_range(desired_genre, desired_start_year, desired_end_year, desired_offsets)
"""
# Print the list of artists
#print(artists_list)

def get_artist_info(artist_name):
    # Search for the artist
    results = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
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

def create_artists_dataframe(artists_list):
    # Use ThreadPoolExecutor to parallelize API calls
    with ThreadPoolExecutor() as executor:
        artist_data = list(executor.map(get_artist_info, artists_list))
        df = pd.DataFrame(artist_data)

    return df

# Example usage with your artists_list
  # Your long list of artists
#artists_df = create_artists_dataframe(artists_list)

# Print the DataFrame
#artists_df

@app.route('/callback', methods=['GET'])
def callback():
    # Process the callback here (e.g., handle the authentication code)
    # You may need to exchange the code for an access token, depending on your OAuth flow.

    # Example: Extract the code from the URL parameters
    code = request.args.get('code')

    # Further processing...

    return 'Callback received successfully!'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
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

        # Create the artists DataFrame
        artists_df = create_artists_dataframe(artists_list)

        # Convert DataFrame to HTML table
        artists_table = artists_df.to_html(classes='table table-striped', index=False)

        return render_template('result.html', table=artists_table)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(port=8000)