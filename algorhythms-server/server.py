import socket
import threading
from typing import Any, List, Optional, Union
from fastapi import FastAPI, Request as FastAPIRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn 
from gemini_api import generate_target_features, generate_emoji
from spotify_auth import TokenInfo, get_spotify_clients
from spotify_api import spotify_api_client
from spotipy import Spotify

# Run command: fastapi dev server.py
HOST = "127.0.0.1"
PORT = 8000
uvicorn_server: uvicorn.Server | None = None  # Reference to uvicorn server instance
server_thread: threading.Thread | None= None  # Track server thread

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run_server():
    global uvicorn_server
    
    # Create reusable socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Critical fix
    sock.bind((HOST, PORT))
    sock.listen(5)
    
    config = uvicorn.Config(app, workers=1)
    uvicorn_server = uvicorn.Server(config)
    uvicorn_server.run(sockets=[sock])  # Pass preconfigured socket

def start_server():
    global server_thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print(f"Server started on http://{HOST}:{PORT}")
    return server_thread

def stop_server():
    global uvicorn_server, server_thread
    if uvicorn_server:
        uvicorn_server.should_exit = True
        print("Server shutdown initiated")
        
        # Wait for thread to finish with timeout
        if server_thread and server_thread.is_alive():
            server_thread.join(timeout=3.0)
            if server_thread.is_alive():
                print("Warning: Server thread did not terminate in time")
    
    # Clean up references
    uvicorn_server = None
    server_thread = None

@app.get("/")
def root_endpoint():
        return {"status": "success"}

@app.get("/generate-target-features")
async def generate_weights_endpoint(mood: Union[str, None] = None, activity: Union[str, None] = None):
    if(mood is not None and activity is not None):
        return await generate_target_features(mood, activity)
    else:
        return {"error": "Activity or Mood is undefined"}
    
@app.get("/generate-emoji")
async def generate_emoji_endpoint(term: Union[str, None] = None):
    if(term is not None):
        return {"emoji": await generate_emoji(term)}
    else:
        return {"error": "term is undefined"}
    
@app.get("/search-tracks")
async def search_tracks_endpoint(query: Union[str, None] = None):
    server_access, _ = await get_spotify_clients()
    if(query is not None):
        return await spotify_api_client.search_tracks(server_access, query)
    else:
        return {"error": "No search query specified"}

@app.get("/server_auth_callback", response_class=HTMLResponse)
def server_auth_callback_endpoint(code: str, state: str):
    """
    Handles the redirect from Spotify after user authorization.
    """
    from spotify_auth import _active_authenticator
    
    # Check if an authentication process is active
    if _active_authenticator is None:
        return """
        <h1>Error: No active authentication process.</h1>
        <p>This can happen if the server was restarted or the authentication timed out. Please try again.</p>
        """

    try:
        print(f"Received callback with code: {code[:10]}... and state: {state}")
        
        # Call the method on the shared instance. This will set the event
        # that the get_spotify_clients() function is waiting on.
        _active_authenticator.handle_auth_callback(code, state)

        # Return a success message to the user's browser
        return """
        <h1>Authentication Successful!</h1>
        <p>You can now close this browser tab and return to the application.</p>
        <script>window.close();</script>
        """
    except Exception as e:
        print(f"Error handling callback: {str(e)}")
        return f"""
        <h1>Authentication Failed</h1>
        <p>An error occurred: {str(e)}</p>
        <p>Please try the process again.</p>
        """

class PlaylistRequest (BaseModel):
    targetFeatures: Any
    weights: Any
    auth: Optional[TokenInfo] = None
@app.post("/generate-playlist")
async def generate_playlist_endpoint(
    fastapi_request: FastAPIRequest,
    request: PlaylistRequest,
    mood: Optional[str] = None,
    activity: Optional[str] = None,
    length: Optional[str] = None,
    favorite_songs: Optional[str] = None
):
    from generate_playlist import task_generator
    
    from spotify_auth import get_client_from_user_token

    if(mood is None or activity is None or length is None):
        return {
            "error":"mood, activity, or length cannot be none"
        }

    # Split comma-separated favorite_songs into a list
    favorite_songs_list: Optional[List[str]] = None
    if(favorite_songs is not None):
        favorite_songs_list = favorite_songs.split(',')

    sp: Spotify
    if( request.auth is not None):
        sp = get_client_from_user_token(request.auth)
    else:
        _, sp = await get_spotify_clients()

    return StreamingResponse(
        task_generator(fastapi_request, sp, favorite_songs_list),
        media_type="application/x-ndjson",  # Newline-delimited JSON
        headers={"Cache-Control": "no-cache"}
    )