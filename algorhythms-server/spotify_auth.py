import random
import string
import threading
import time
import webbrowser
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from spotipy.cache_handler import CacheFileHandler, MemoryCacheHandler
from typing import cast

REDIRECT_URI = "http://127.0.0.1:8000/server_auth_callback"
TOKEN_CACHE_PATH = "spotify_token_cache.txt"

load_dotenv(dotenv_path='./secrets.env')
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

server_access = Spotify(auth_manager=SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret,
    ))

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
        scope=" ".join(scopes),
        cache_handler=CacheFileHandler(cache_path=TOKEN_CACHE_PATH),
        state=random_id()
    )

def try_initialize_from_cache() -> bool:
    """Attempt to initialize from cached token and refresh if needed""" 
    oauth = initialize_oauth()

    # Try to get cached token  and ensure scope is current
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
    algorhythms_account.auth_manager = oauth
    token_obtained_event.set()
    return True

def prompt_spotify_login() -> None:
    oauth = initialize_oauth()
    auth_url = oauth.get_authorize_url()
    algorhythms_account.auth_manager = oauth
    print(f"Opening browser for Spotify login: {auth_url}")
    webbrowser.open(auth_url, new=2, autoraise=True)

def handle_auth_callback(code: str, state: str) -> None:
    if algorhythms_account.auth_manager is None:
        raise RuntimeError("OAuth not initialized when handling callback")
    
    oauth = cast(SpotifyOAuth, algorhythms_account.auth_manager)
    
    # Validate state
    if state != oauth.state:
        raise ValueError("State parameter does not match server's state")
    
    # Exchange auth code for tokens
    oauth.get_access_token(code)
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

def initialize_algorithms_account():
    # First try to initialize from cache
        if try_initialize_from_cache():
            print("\nAuthenticated with cached token!")
        else:
            # Fallback to regular login flow
            prompt_spotify_login()
            print("Waiting for authentication...")
            
            # Wait for token exchange to complete (timeout after 5 minutes)    
            if wait_for_auth(300):
                print("\nAuthentication flow completed successfully!")
            else:
                print("\nAuthentication timed out. Please try again.")

class TokenInfo(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    expires_at: int
    refresh_token: str
    scope: str
def get_access_from_user_token(token_info: TokenInfo) -> Spotify:
    print(token_info.expires_at)
    oauth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_id, 
        redirect_uri=REDIRECT_URI, 
        cache_handler=MemoryCacheHandler(token_info=token_info.model_dump()), 
        scope=token_info.scope, 
        open_browser=False
    )
    return Spotify(auth_manager=oauth)