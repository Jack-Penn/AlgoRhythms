import asyncio
from datetime import datetime
from pydantic import BaseModel, EmailStr
from spotipy import Spotify
from typing import List, Literal, Optional, Union, Callable, Dict, List, Any
from _types import *

# --- Type Definitions ---

class ExternalUrls(BaseModel):
    """Known external URLs for a Spotify object."""
    spotify: Optional[str] = None

class SpotifyImageObject(BaseModel):
    """Image for a Spotify object."""
    url: str
    height: Optional[int] = None
    width: Optional[int] = None

class SimplifiedArtistObject(BaseModel):
    """Simplified Artist Object for lists."""
    external_urls: ExternalUrls
    href: Optional[str] = None
    id: Optional[str] = None
    name: str
    type: Literal["artist"]
    uri: Optional[str] = None

class Restrictions(BaseModel):
    """Content restriction information."""
    reason: Literal["market", "product", "explicit"]

class SpotifyAlbum(BaseModel):
    """Album on which a track appears."""
    album_type: Literal["album", "single", "compilation"]
    total_tracks: int
    available_markets: List[str]
    external_urls: ExternalUrls
    href: str
    id: str
    images: List[SpotifyImageObject]
    name: str
    release_date: str
    release_date_precision: Literal["year", "month", "day"]
    restrictions: Optional[Restrictions] = None
    type: Literal["album"]
    uri: str
    artists: List[SimplifiedArtistObject]

class ExternalIds(BaseModel):
    """Known external IDs for a track."""
    isrc: Optional[str] = None
    ean: Optional[str] = None
    upc: Optional[str] = None

class SpotifyTrack(BaseModel):
    """Detailed information about a track."""
    album: SpotifyAlbum
    artists: List[SimplifiedArtistObject]
    available_markets: Optional[List[str]] = []
    disc_number: int
    duration_ms: int
    explicit: bool
    external_ids: Optional[ExternalIds] = None
    external_urls: ExternalUrls
    href: str
    id: SpotifyTrackID
    is_playable: Optional[bool] = None
    restrictions: Optional[Restrictions] = None
    name: str
    popularity: int
    preview_url: Optional[str] = None
    track_number: int
    type: Literal["track"]
    uri: str
    is_local: bool = False

class SpotifyEpisode(BaseModel):
    """Placeholder for an Episode Object."""
    id: str
    name: str
    type: Literal["episode"]
    uri: str

class ExplicitContent(BaseModel):
    """User's explicit content settings."""
    filter_enabled: bool
    filter_locked: bool

class Followers(BaseModel):
    """Information about the followers of a user."""
    href: Optional[str] = None
    total: int

class SpotifyUser(BaseModel):
    """A full Spotify User object."""
    country: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    explicit_content: Optional[ExplicitContent] = None
    external_urls: ExternalUrls
    followers: Followers
    href: str
    id: str
    images: List[SpotifyImageObject]
    product: Optional[str] = None
    type: Literal["user"]
    uri: str

class AddedBy(BaseModel):
    """The Spotify user who added the track or episode."""
    external_urls: ExternalUrls
    href: str
    id: str
    type: Literal["user"]
    uri: str

class PlaylistTrack(BaseModel):
    """An item in a playlist's track list."""
    added_at: Optional[datetime] = None
    added_by: Optional[AddedBy] = None
    is_local: bool
    track: Union[SpotifyTrack, SpotifyEpisode]

class Tracks(BaseModel):
    """The tracks of the playlist in a paging object."""
    href: str
    total: int

class PlaylistOwner(BaseModel):
    """The user who owns the playlist."""
    external_urls: ExternalUrls
    href: str
    id: str
    type: Literal["user"]
    uri: str
    display_name: Optional[str] = None

# class PlaylistTrack
class SpotifyPlaylist(BaseModel):
    """A full Spotify Playlist object."""
    collaborative: bool
    description: Optional[str] = None
    external_urls: ExternalUrls
    href: str
    id: str
    images: List[SpotifyImageObject]
    name: str
    owner: PlaylistOwner
    public: Optional[bool] = None
    snapshot_id: str
    tracks: Tracks
    type: Literal["playlist"]
    uri: str


# --- Client Functions ---
class SpotifyAPIClient:
    """Client for interacting with Spotify API"""
    def __init__(self, concurrent_request_limit: int = 20):
        self.semaphore = asyncio.Semaphore(concurrent_request_limit)

    async def _make_request(self, blocking_func: Callable) -> Optional[Dict[str, Any]]:
        async with self.semaphore:
            response = await asyncio.to_thread(blocking_func)
        if response is None:
            print("Error making request", blocking_func)
        return response
    
    async def _handle_pagination(
        self,
        func: Callable,
        args: Dict[str, Any],
        limit: int,
        max_per_page: int = 50,
        extract_items: Callable[[Dict[str, Any]], Any] = lambda response: [response]
    ) -> List[Dict[str, Any]]:
        """
        Generic pagination handler for API functions that support offset/limit parameters.
        
        Args:
            func: API function to call (must accept offset/limit parameters)
            args: Dictionary of base arguments to pass to the function
            limit: Total number of items to retrieve
            max_per_page: Maximum items per request (default 50)
        
        Returns:
            Combined list of items from all paginated requests
        """
        # Calculate required pages
        pages: List[tuple[int, int]] = [] #represensts offset, page size
        remaining = limit
        offset = 0
        
        while remaining > 0:
            page_limit = min(remaining, max_per_page)
            pages.append((offset, page_limit))
            offset += page_limit
            remaining -= page_limit
        
        # Worker function for single page request
        async def fetch_page(offset_val: int, limit_val: int) -> List[Any]:
            # Merge base args with pagination parameters
            params = {**args, "offset": offset_val, "limit": limit_val}
            response = await self._make_request(lambda: func(**params))
            if not response:
                return []
            try:
                items = extract_items(response)
                return items
            except Exception as e:
                print(e)
                return []
        
        # Execute requests concurrently
        page_tasks = [fetch_page(offset, page_limit) for offset, page_limit in pages]
        list_of_page_results = await asyncio.gather(*page_tasks)
        all_items = [item for page in list_of_page_results for item in page]

        return all_items

    async def get_user(self, sp: Spotify) -> Optional[SpotifyUser]:
        user_response = await self._make_request(sp.current_user)
        if not user_response:
            print("Error creating fetching user")
            return None
        return SpotifyUser(**user_response)

    async def create_playlist(self, sp: Spotify, playlist_name: str, description:str, track_uris: List[SpotifyTrackURI]) -> Optional[SpotifyPlaylist]:
        user = await self.get_user(sp)
        if not user:
            return
        playlist_response = await self._make_request(lambda: sp.user_playlist_create(user.id, playlist_name, public=True, description=description))
        if not playlist_response:
            print("Error creating playlist")
            return None
        playlist = SpotifyPlaylist(**playlist_response)
        await self._make_request(lambda: sp.playlist_add_items(playlist.id, track_uris))
        return playlist

    async def get_top_tracks(self, sp:Spotify, limit: int, time_range: Literal["short_term", "medium_term", "long_term"] ="medium_term") -> List[SpotifyTrack]:
        items = await self._handle_pagination(
            func=sp.current_user_top_tracks,
            args={"time_range": time_range},
            limit=limit,
            extract_items=lambda response: response["items"]
        )
        return [SpotifyTrack(**item) for item in items]

    async def get_saved_tracks(self, sp: Spotify, limit: int) -> List[SpotifyTrack]:
        items = await self._handle_pagination(
            func=sp.current_user_saved_tracks,
            args={},
            limit=limit,
            extract_items=lambda response: response["items"]
        )
        return [SpotifyTrack(**item["track"]) for item in items]

    async def search_tracks(self, sp: Spotify, query: str, limit: int = 10) -> List[SpotifyTrack]:
        items = await self._handle_pagination(
            func=sp.search,
            args={
                "q": query,
                "type": "track"
            },
            limit=limit,
            extract_items=lambda response: response["tracks"]["items"]
        )
        tracks = [SpotifyTrack(**item) for item in items]
        return self.deduplicate_tracks(tracks)

    async def get_tracks_details(self, sp: Spotify, track_ids: List[SpotifyTrackID]):
        response = await self._make_request(lambda: sp.tracks(track_ids))
        if not response:
            return
        return [SpotifyTrack(**track) for track in response["tracks"]]

    def deduplicate_tracks(self, tracks: List[SpotifyTrack]) -> list[SpotifyTrack]:
        seen: set[SpotifyTrackID] = set()
        unique_tracks = []
        
        for track in tracks:
            key = track.id
            # Add first occurrence of each unique track
            if key not in seen:
                seen.add(key)
                unique_tracks.append(track)
                
        return unique_tracks

    async def search_playlist(self, sp: Spotify, query: str, limit: int = 10) -> List[SpotifyPlaylist]:
        items = await self._handle_pagination(
            func=sp.search,
            args={
                "q": query,
                "type": "playlist",
                "market": "US"
            },
            limit=limit,
            extract_items=lambda response: response["playlists"]["items"]
        )
        return  [SpotifyPlaylist(**item) for item in items if item] # Filter out None values

    async def get_playlist_items(self, sp: Spotify, playlist_id: str, limit: int):
        items = await self._handle_pagination(
            func=sp.playlist_items,
            args={
                "playlist_id": playlist_id
            },
            limit=limit,
            extract_items=lambda response: response["items"]
        )
        return [SpotifyTrack(**item["track"]) for item in items if item and item.get("track")]


spotify_api_client = SpotifyAPIClient() # exported shared client instance

# --- Test Functions ---

async def test_create_playlist(client: SpotifyAPIClient, sp: Spotify):
    print("--- Testing Playlist Creation ---")
    spotify_ids = [SpotifyTrackID("2ipIPsgrgd0j2beDf4Ki70"), SpotifyTrackID("42UBPzRMh5yyz0EDPr6fr1"), SpotifyTrackID("102YUQbYmwdBXS7jwamI90")]
    playlist = await client.create_playlist(sp, "Test Playlist", "Test Desc", [spotify_id.get_uri() for spotify_id in spotify_ids])
    if playlist:
        print(f"Playlist Created: '{playlist.name}'")
    else:
        print("Failed.")
    print("-" * 30)

async def test_get_top_tracks(client: SpotifyAPIClient, sp: Spotify):
    print("--- Testing Get Top Tracks ---")
    tracks = await client.get_top_tracks(sp, limit=5, time_range="medium_term")
    print(f"Found {len(tracks)} top tracks.")
    for t in tracks: print(f"  - {t.name}")
    print("-" * 30)

async def test_get_saved_tracks(client: SpotifyAPIClient, sp: Spotify):
    print("--- Testing Get Saved Tracks ---")
    tracks = await client.get_saved_tracks(sp, limit=5)
    print(f"Found {len(tracks)} saved tracks.")
    for t in tracks: print(f"  - {t.name}")
    print("-" * 30)

async def test_search_tracks(client: SpotifyAPIClient, sp: Spotify):
    print("--- Testing Track Search ---")
    tracks = await client.search_tracks(sp, "Daft Punk", limit=5)
    print(f"Found {len(tracks)} tracks.")
    for t in tracks: print(f"  - {t.name}")
    print("-" * 30)

async def test_search_playlist(client: SpotifyAPIClient, sp: Spotify):
    print("--- Testing Playlist Search ---")
    playlists = await client.search_playlist(sp, "Chill", limit=10)
    print(f"Found {len(playlists)} playlists.")
    for p in playlists: print(f"  - {p.name}")
    print("-" * 30)

async def main():
    from spotify_auth import get_spotify_clients
    client = SpotifyAPIClient()
    _, algorithms_account = await get_spotify_clients()
    sp = algorithms_account

    await test_create_playlist(client, sp)
    await test_get_top_tracks(client, sp)
    await test_get_saved_tracks(client, sp)
    await test_search_tracks(client, sp)
    await test_search_playlist(client, sp)

if __name__ == "__main__":
    asyncio.run(main())