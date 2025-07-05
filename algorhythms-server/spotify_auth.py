import random
import string
import threading
import time
import webbrowser
from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheFileHandler

REDIRECT_URI = "http://127.0.0.1:8000/server_auth_callback"
TOKEN_CACHE_PATH = "spotify_token_cache.txt"

load_dotenv(dotenv_path='./secrets.env')
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

scopes = ["user-library-read", "user-top-read", "playlist-modify-public", "playlist-modify-private"]

# Global variables for Spotify auth
oauth: SpotifyOAuth | None = None
sp = None
token_obtained_event = threading.Event() # Used for tracking auth timeout

def initialize_oauth():
    """Initialize SpotifyOAuth with file-based caching"""
    global oauth

    def random_id(size=16, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    oauth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=REDIRECT_URI,
        scope="  ".join(scopes),
        cache_handler=CacheFileHandler(cache_path=TOKEN_CACHE_PATH),  # File-based cache
        state=random_id()
    )
    return oauth

def try_initialize_from_cache():
    """Attempt to initialize from cached token and refresh if needed"""
    global oauth, sp
    
    # Initialize oauth if not done
    if oauth is None:
        oauth = initialize_oauth()
    
    # Try to get cached token
    token_info = oauth.get_cached_token()
    if not token_info:
        return False
        
    # Check if token needs refresh
    if oauth.is_token_expired(token_info):
        try:
            token_info = oauth.refresh_access_token(token_info['refresh_token'])
        except Exception as e:
            print(f"Token refresh failed: {str(e)}")
            return False
    
    # Initialize Spotify client
    sp = spotipy.Spotify(auth_manager=oauth)
    token_obtained_event.set()
    return True


def prompt_spotify_login():
    global oauth, sp
    oauth = initialize_oauth()
    auth_url = oauth.get_authorize_url()
    print(f"Opening browser for Spotify login: {auth_url}")
    webbrowser.open(auth_url, new=2, autoraise=True)

def handle_auth_callback(code: str, state: str):
    global sp

    # Validate state
    if(state != oauth.state):
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
        # This will automatically refresh and update cache
        token_info = oauth.get_cached_token()
        if token_info:
            token_info = oauth.refresh_access_token(token_info['refresh_token'])
            sp = spotipy.Spotify(auth_manager=oauth)
            print("Token refreshed successfully")
            return True
    return False