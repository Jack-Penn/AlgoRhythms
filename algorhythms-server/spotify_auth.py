import asyncio
import os
import random
import string
import threading
import webbrowser
from typing import cast

from dotenv import load_dotenv
from pydantic import BaseModel
from spotipy import Spotify
from spotipy.cache_handler import CacheFileHandler, MemoryCacheHandler
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from spotify_api import spotify_api_client

# --- 1. Configuration ---
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


# --- 2. Data Models ---

class TokenInfo(BaseModel):
    """Pydantic model for validating token data."""
    access_token: str
    token_type: str
    expires_in: int
    expires_at: int
    refresh_token: str
    scope: str


# --- 3. Authenticator Class ---

class SpotifyUserAuthenticator:
    """Handles the Spotify user authentication flow."""

    def __init__(self):
        self.client = Spotify()
        self.token_obtained_event = threading.Event()

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

    def _wait_for_auth(self, timeout: int = 300) -> bool:
        """Waits for the authentication callback to be handled."""
        print("Waiting for authentication...")
        try:
            return self.token_obtained_event.wait(timeout=timeout)
        except KeyboardInterrupt:
            print("\nAuthentication wait cancelled by user.")
            return False

    def authenticate(self) -> Spotify:
        """
        Main method to orchestrate the authentication process.
        
        Returns a fully authenticated Spotipy client instance.
        """
        if self._try_auth_from_cache():
            print("\nAuthenticated successfully using cached token!")
        else:
            self._prompt_user_login()
            if self._wait_for_auth():
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


# --- 4. Standalone Utilities ---

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


# --- 5. Example Usage ---

async def main():
    # Example of getting a user-authenticated client
    authenticator = SpotifyUserAuthenticator()
    
    # In a real app, you'd run the web server in a separate thread
    # and call handle_auth_callback from the server's route handler.
    # For this example, we'll just run the authentication flow.
    
    algorhythms_account = authenticator.authenticate()

    user = None

    # Now `algorhythms_account` is ready to use
    if authenticator.token_obtained_event.is_set():
        user = await spotify_api_client.get_user(algorhythms_account)

    if user:
        print(f"\nSuccessfully authenticated as: {user.display_name} ({user.id})")
    else:
        print("\nCould not authenticate.")

    # Example of getting a server-to-server client
    server_client = get_server_access_client()
    print("\nServer-to-server client created.")

if __name__ == "__main__":
    asyncio.run(main())