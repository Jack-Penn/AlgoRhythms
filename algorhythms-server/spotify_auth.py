import random
import string
import threading
import time
import webbrowser
from dotenv import load_dotenv
import os
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from spotipy.cache_handler import CacheFileHandler
from typing import cast

REDIRECT_URI = "http://127.0.0.1:8000/server_auth_callback"
TOKEN_CACHE_PATH = "spotify_token_cache.txt"

load_dotenv(dotenv_path='./secrets.env')
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

scopes = ["user-library-read", "user-top-read", "playlist-modify-public", "playlist-modify-private"]

# Global container for Spotify account
algorhythms_account = Spotify()

token_obtained_event = threading.Event()

def initialize_oauth() -> SpotifyOAuth:
    """Initialize SpotifyOAuth with file-based caching"""
    def random_id(size: int = 16, chars: str = string.ascii_uppercase + string.digits) -> str:
        return ''.join(random.choice(chars) for _ in range(size))

    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=REDIRECT_URI,
        scope="  ".join(scopes),
        cache_handler=CacheFileHandler(cache_path=TOKEN_CACHE_PATH),
        state=random_id()
    )

def try_initialize_from_cache() -> bool:
    """Attempt to initialize from cached token and refresh if needed""" 
    oath = initialize_oauth()

    # Try to get cached token
    token_info = oath.get_cached_token()
    if not token_info:
        return False
        
    # Check if token needs refresh
    if oath.is_token_expired(token_info):
        try:
            token_info = oath.refresh_access_token(token_info['refresh_token'])
        except Exception as e:
            print(f"Token refresh failed: {str(e)}")
            return False
    
    # Initialize Spotify client
    algorhythms_account.auth_manager = oath
    token_obtained_event.set()
    return True

def prompt_spotify_login() -> None:
    oath = initialize_oauth()
    auth_url = oath.get_authorize_url()
    algorhythms_account.auth_manager = oath
    print(f"Opening browser for Spotify login: {auth_url}")
    webbrowser.open(auth_url, new=2, autoraise=True)

def handle_auth_callback(code: str, state: str) -> None:
    if algorhythms_account.auth_manager is None:
        raise RuntimeError("OAuth not initialized when handling callback")
    
    oath = cast(SpotifyOAuth, algorhythms_account.auth_manager)
    
    # Validate state
    if state != oath.state:
        raise ValueError("State parameter does not match server's state")
    
    # Exchange auth code for tokens
    oath.get_access_token(code)
    token_obtained_event.set()

def wait_for_auth(timeout: int = 300) -> bool:
    """Wait for authentication with keyboard interrupt support"""
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

# def refresh_token() -> bool:
#     if not oauth_initialized() or not sp_initialized():
#         return False
    
#     oauth_obj = cast(SpotifyOAuth, algorhythms_account["oauth"])
    
#     # This will automatically refresh and update cache
#     token_info = oauth_obj.get_cached_token()
#     if token_info:
#         try:
#             token_info = oauth_obj.refresh_access_token(token_info['refresh_token'])
#             algorhythms_account["sp"] = spotipy.Spotify(auth_manager=oauth_obj)
#             print("Token refreshed successfully")
#             return True
#         except Exception as e:
#             print(f"Token refresh failed: {str(e)}")
#     return False

server_access = Spotify(auth_manager=SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret,
    ))