from spotipy import Spotify
from typing import List
from spotify_auth import algorhythms_account

def create_playlist(sp: Spotify, name: str, description:str, track_uris: List[str]):
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
def searchTracks(sp: Spotify, query: str):
    response = sp.search(query, type="track")
    if response is None:
            print("Error: Received no response from Spotify API")
            return
    return deduplicate_tracks(response["tracks"]["items"])

