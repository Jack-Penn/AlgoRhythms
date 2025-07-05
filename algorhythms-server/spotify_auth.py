import random
import string
import threading
import time
import webbrowser
from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

REDIRECT_URI = "http://127.0.0.1:8000/server_auth_callback"

load_dotenv(dotenv_path='./secrets.env')
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

scopes = ["user-library-read", "user-top-read", "playlist-modify-public", "playlist-modify-private"]

# Global variables for Spotify auth
oauth: SpotifyOAuth | None = None
sp = None
state_check = None
token_obtained_event = threading.Event() # Used for tracking auth timeout

def prompt_spotify_login():
    global oauth, sp, state_check

    def random_id(size=16, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))
    state_check = random_id()

    oauth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=REDIRECT_URI,
        state=state_check,
        scope="  ".join(scopes),
        cache_handler=spotipy.cache_handler.MemoryCacheHandler(),  # Use in-memory cache
    )
    auth_url = oauth.get_authorize_url()
    print(f"Opening browser for Spotify login: {auth_url}")
    webbrowser.open(auth_url, new=2, autoraise=True)

def handle_auth_callback(code: str, state: str):
    global sp

    # Validate state
    if(state != state_check):
        raise ValueError("State parameter does not match server's state")
    
    # Exchange auth code for tokens
    token_info = oauth.get_access_token(code)
    sp = spotipy.Spotify(auth_manager=oauth)
    token_obtained_event.set()

def wait_for_auth(timeout=300):
    """Wait for authentication with keyboard interrupt support"""
    global token_obtained_event
    start_time = time.time()
    
    while not token_obtained_event.is_set():
        elapsed = time.time() - start_time
        if elapsed >= timeout:
            return False
        
        try:
            # Wait in small intervals to allow keyboard interrupts
            token_obtained_event.wait(timeout=min(1, timeout - elapsed))
        except KeyboardInterrupt:
            print("\nAuthentication wait cancelled by user")
            return False
    return True

def refresh_token():
    global oauth, sp
    if oauth and sp:
        token_info = oauth.refresh_access_token(oauth.get_cached_token()['refresh_token'])
        sp = spotipy.Spotify(auth_manager=oauth)
        print("Token refreshed successfully")
        return True
    return False