from typing import List, Optional, cast
from pydantic import BaseModel
import spotify_auth 

class Image(BaseModel):
    url: str
    height: int
    width: int

class ExplicitContent(BaseModel):
    filter_enabled: bool
    filter_locked: bool

class ExternalUrls(BaseModel):
    spotify: str

class Followers(BaseModel):
    href: Optional[str] = None
    total: int

class UserProfile(BaseModel):
    country: str
    display_name: str
    email: str
    explicit_content: ExplicitContent
    external_urls: ExternalUrls
    followers: Followers
    href: str
    id: str
    images: List[Image]
    product: str
    type: str
    uri: str

current_user = None

def create_playlist(track_uris: List[str]):
    global current_user
    print(spotify_auth.sp)
    if current_user is None:
        current_user = spotify_auth.sp.current_user()
        print(current_user)
    print("Creating test playlist")
    playlist_id = spotify_auth.sp.user_playlist_create(current_user['id'], "Programatic Playlist", public=True, description="This playlist was created with python")["id"]
    spotify_auth.sp.playlist_add_items(playlist_id, track_uris)

def print_top_tracks():
    # Get top 10 tracks
    top_tracks = spotify_auth.sp.current_user_top_tracks(limit=10, time_range="medium_term")
    
    # Print results
    print("\nYour Top 10 Tracks:")
    for idx, track in enumerate(top_tracks["items"]):
        artists = ", ".join([artist["name"] for artist in track["artists"]])
        print(f"{idx+1}. {track['name']} by {artists}")