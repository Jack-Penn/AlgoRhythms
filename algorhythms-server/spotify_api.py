from spotipy import Spotify
from typing import List, Literal
from spotify_auth import algorhythms_account
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Any

def create_playlist(sp: Spotify, name: str, description:str, track_uris: List[str]) -> dict | None:
    current_user = sp.current_user()
    if current_user is None:
        print("Error: Received no response from Spotify API while getting current user")
        return
    print(current_user)
    print("Creating test playlist")
    playlist = algorhythms_account.user_playlist_create(current_user["id"], name, public=True, description=description)
    if playlist is None:
        print("Error creating playlist")
        return
    sp.playlist_add_items(playlist["id"], track_uris)
    return playlist

def handle_pagination(
    func: Callable,
    args: Dict[str, Any],
    limit: int,
    max_per_page: int = 50
) -> List[Any]:
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
    pages = []
    remaining = limit
    offset = 0
    
    while remaining > 0:
        page_limit = min(remaining, max_per_page)
        pages.append((offset, page_limit))
        offset += page_limit
        remaining -= page_limit
    
    # Worker function for single page request
    def fetch_page(offset_val: int, limit_val: int) -> List[Any]:
        # Merge base args with pagination parameters
        params = {**args, "offset": offset_val, "limit": limit_val}
        response = func(**params)
        return response.get("items", []) if response else []
    
    # Execute requests concurrently
    all_items = []
    with ThreadPoolExecutor() as executor:
        # Submit all page requests to thread pool
        futures = [executor.submit(fetch_page, offset, page_limit)  for offset, page_limit in pages]
        
        # Collect results in order
        for future in futures:
            all_items.extend(future.result())
    
    return all_items

def get_top_tracks(sp:Spotify, limit, time_range: Literal["short_term", "medium_term", "long_term"] ="medium_term"):
    return handle_pagination(
        func=sp.current_user_top_tracks,
        args={"time_range": time_range},
        limit=limit
    )

def get_saved_tracks(sp: Spotify, limit):
    return [item["track"] for item  in handle_pagination(
        func=sp.current_user_saved_tracks,
        args={},
        limit=limit
    )]

def print_top_tracks(sp: Spotify):
    # Get top 10 tracks
    response = sp.current_user_top_tracks(limit=10, time_range="medium_term")
    if response is None:
            print("Error: Received no response from Spotify API")
            return
    print("\nYour Top 10 Tracks:")
    for idx, track in enumerate(response['items']):
        artists = ", ".join([artist["name"] for artist in track["artists"]])
        print(f"{idx+1}. {track['name']} by {artists}")

def deduplicate_tracks(tracks: list[dict]) -> list[dict]:
    seen = set()
    unique_tracks = []
    
    for track in tracks:
        # Extract and normalize track name
        track_name = track['name'].lower()
        
        # Extract, normalize, and sort artist names
        artists = sorted([a['name'].lower() for a in track['artists']])
        artist_key = ','.join(artists)
        
        # Create unique composite key
        composite_key = f"{track_name}|{artist_key}"
        
        # Add first occurrence of each unique track
        if composite_key not in seen:
            seen.add(composite_key)
            unique_tracks.append(track)
            
    return unique_tracks
def search_tracks(sp: Spotify, query: str):
    response = sp.search(query, type="track")
    if response is None:
            print("Error: Received no response from Spotify API")
            return
    return deduplicate_tracks(response["tracks"]["items"])

def search_playlist(sp: Spotify, query: str, limit: int) -> list[dict]:
    response = sp.search(query, type="playlist", limit=limit,)
     # Handle API errors or empty responses
    if not response or "playlists" not in response:
        print("Error: Invalid response structure from Spotify API")
        return []
    
    # Extract playlist items
    items = response["playlists"].get("items", [])
    
    # Filter out None values and ensure items are dictionaries
    valid_items = [item for item in items if item]
    
    return valid_items
