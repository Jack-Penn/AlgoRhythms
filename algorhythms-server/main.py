from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv(dotenv_path='./secrets.env')
client_id = os.getenv("SPOTIFY_CLIENT_ID")

print(client_id)

# sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="client_id",
#                                                            client_secret="YOUR_APP_CLIENT_SECRET"))

# results = sp.search(q='weezer', limit=20)
# for idx, track in enumerate(results['tracks']['items']):
#     print(idx, track['name'])