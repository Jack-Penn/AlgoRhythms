import asyncio
import os
import random
import string
import threading
import webbrowser
from typing import Tuple, cast

from dotenv import load_dotenv
from pydantic import BaseModel
from spotipy import Spotify
from spotipy.cache_handler import CacheFileHandler, MemoryCacheHandler
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

# --- Configuration ---
# Load environment variables from a .env file
load_dotenv(dotenv_path='./secrets.env')

# Spotify App Credentials
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# OAuth Settings
REDIRECT_URI = "http://127.0.0.1:8000/server_auth_callback"
SCOPES = [
    "user-library-read",
    "user-top-read",
    "playlist-modify-public",
    "playlist-modify-private"
]
TOKEN_CACHE_PATH = "spotify_token_cache.txt"


# --- Data Models ---

class TokenInfo(BaseModel):
    """Pydantic model for validating token data."""
    access_token: str
    token_type: str
    expires_in: int
    expires_at: int
    refresh_token: str
    scope: str


# --- Authenticator Class ---

class SpotifyUserAuthenticator:
    """Handles the Spotify user authentication flow."""

    def __init__(self):
        self.client = Spotify()
        self.token_obtained_event = asyncio.Event()

    def _initialize_oauth(self) -> SpotifyOAuth:
        """Creates and returns a SpotifyOAuth instance."""
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
        return SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=" ".join(SCOPES),
            cache_handler=CacheFileHandler(cache_path=TOKEN_CACHE_PATH),
            state=state
        )

    def _try_auth_from_cache(self) -> bool:
        """
        Attempts to authenticate using a cached token. Refreshes the token if expired.
        Returns True on success, False on failure.
        """
        oauth = self._initialize_oauth()
        token_info = oauth.get_cached_token()

        if not token_info:
            return False

        if oauth.is_token_expired(token_info):
            try:
                refresh_token = token_info.get('refresh_token')
                if refresh_token:
                    token_info = oauth.refresh_access_token(refresh_token)
                else:
                    return False # Cannot refresh without a refresh token
            except Exception as e:
                print(f"Token refresh failed: {e}")
                return False
        
        self.client.auth_manager = oauth
        self.token_obtained_event.set()
        return True

    def _prompt_user_login(self) -> None:
        """Opens a browser for the user to log in and authorize."""
        oauth = self._initialize_oauth()
        auth_url = oauth.get_authorize_url()
        self.client.auth_manager = oauth
        
        print(f"Opening browser for Spotify login: {auth_url}")
        webbrowser.open(auth_url, new=2, autoraise=True)

    async def _wait_for_auth(self, timeout: int = 300) -> bool:
        """Waits asynchronously for the authentication callback."""
        print("Waiting for authentication...")
        try:
            # await the asyncio.Event
            await asyncio.wait_for(self.token_obtained_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            print("\nAuthentication timed out.")
            return False
        except KeyboardInterrupt:
            print("\nAuthentication wait cancelled by user.")
            return False

    async def authenticate(self) -> Spotify:
        """
        Main method to orchestrate the authentication process.
        Returns a fully authenticated Spotipy client instance.
        """
        if self._try_auth_from_cache():
            print("\nAuthenticated successfully using cached token!")
        else:
            self._prompt_user_login()
            if await self._wait_for_auth():
                print("\nAuthentication flow completed successfully!")
            else:
                print("\nAuthentication timed out or was cancelled.")
        
        return self.client

    def handle_auth_callback(self, code: str, state: str) -> None:
        """
        Handles the redirect from Spotify after user authorization.
        To be called by the web server handling the callback.
        """
        if self.client.auth_manager is None:
            raise RuntimeError("OAuth manager not initialized when handling callback.")
        
        oauth = cast(SpotifyOAuth, self.client.auth_manager)
        if state != oauth.state:
            raise ValueError("State parameter mismatch during authentication.")
        
        oauth.get_access_token(code, as_dict=False) # as_dict=False to store in cache
        self.token_obtained_event.set()


# --- Standalone Utilities ---

def get_server_access_client() -> Spotify:
    """Returns a client authenticated with the Client Credentials Flow (server-to-server)."""
    return Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
    )

def get_client_from_user_token(token_info: TokenInfo) -> Spotify:
    """Returns a client authenticated with a user-provided token."""
    oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        cache_handler=MemoryCacheHandler(token_info=token_info.model_dump()),
        scope=token_info.scope,
        open_browser=False
    )
    return Spotify(auth_manager=oauth)

# --- Asynchronous Initializer ---

# Module-level placeholders for our clients
_server_access: Spotify | None = None
_algorhythms_account: Spotify | None = None

async def get_spotify_clients() -> Tuple[Spotify, Spotify]:
    """
    Initializes and returns the shared Spotify client instances.
    Uses a singleton pattern to ensure initialization happens only once.
    """
    from spotify_api import spotify_api_client

    global _server_access, _algorhythms_account

    # If clients are already initialized, return them immediately
    if _server_access and _algorhythms_account:
        return _server_access, _algorhythms_account

    # Initialize the server-to-server client
    print("Initializing server-to-server client...")
    _server_access = get_server_access_client()
    print("✅ Server-to-server client is ready.")
    print("-" * 20)
    
    # Initialize the user-authenticated client
    print("Initializing user-authenticated client ('algorhythms_account')...")
    _authenticator = SpotifyUserAuthenticator()
    # Use the async version of authenticate
    _algorhythms_account = await _authenticator.authenticate() 

    # Verify user authentication
    if _authenticator.token_obtained_event.is_set():
        try:
            # We need to await get_user now
            user_info = await spotify_api_client.get_user(_algorhythms_account)
            if user_info:
                print(f"✅ User client authenticated for: {user_info.display_name} ({user_info.id})")
        except Exception as e:
            print(f"❌ Could not fetch user info after authentication: {e}")
    else:
        print("❌ User client authentication failed or was cancelled.")
    
    # Ensure clients are not None before returning
    if not _server_access or not _algorhythms_account:
        raise RuntimeError("Failed to initialize Spotify clients.")
        
    return _server_access, _algorhythms_account