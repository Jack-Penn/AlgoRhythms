import socket
import threading
from typing import Union
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn 
from gemini_api import generate_weights, generate_emoji
from spotify_auth import handle_auth_callback, server_access
from spotify_api import *

# Run command: fastapi dev server.py
HOST = "127.0.0.1"
PORT = 8000
uvicorn_server = None  # Reference to uvicorn server instance
server_thread = None  # Track server thread

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

@app.get("/generate-weights")
async def generate_weights_endpoint(mood: Union[str, None] = None, activity: Union[str, None] = None):
    if(mood is not None and activity is not None):
        return await generate_weights(mood, activity)
    else:
        return {"error": "Activity or Mood is undefined"}
    
@app.get("/generate-emoji")
async def generate_emoji_endpoint(term: Union[str, None] = None):
    if(term is not None):
        return await generate_emoji(term)
    else:
        return {"error": "term is undefined"}
    
@app.get("/search-tracks")
async def search_tracks_endpoint(query: Union[str, None] = None):
    if(query is not None):
        return searchTracks(server_access, query)
    else:
        return {"error": "No search query specified"}

@app.get("/server_auth_callback")
def server_auth_callback_endpoint(code: str, state: str):
        try:
             print(f"Received callback with code: {code[:10]}... and state: {state}")
             handle_auth_callback(code, state)
             return {"status": "success"}
        except Exception as e:
             print(f"Error: {str(e)}")
             return {"error": str(e)}

# @app.get("/items/{item_id}")
# async def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}