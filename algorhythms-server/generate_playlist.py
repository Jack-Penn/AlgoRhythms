import asyncio
from functools import partial
import json
import time
from typing import Any, Callable, Coroutine, Dict, List, Set, Tuple
import concurrent.futures
from fastapi import Request
import spotify_api
import recco_beats
from spotipy import Spotify

# Define task functions with dependency handling

async def compile_track_list_task(dependencies: dict) -> Tuple[dict, dict]:
    """Compiles a master track list from various sources with related tracks."""
    spotify_user_access = dependencies["spotify_user_access"]
    track_master_list = []
    target_features: recco_beats.TargetFeatures = {}  # Customizable target features
    
    # Shared state for concurrent operations
    CONCURRENT_SPOTIFY_API_LIMIT = 10
    spotify_shared_semaphore = asyncio.Semaphore(CONCURRENT_SPOTIFY_API_LIMIT)
    recco_track_seeds: Set[str] = set()
    known_track_ids: Set[str] = set()  # Tracks we already have or are fetching

    seed_lock = asyncio.Lock()
    track_list_lock = asyncio.Lock()
    known_track_lock = asyncio.Lock()  # For known_track_ids synchronization

    async def fetch_track_details(track_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetches full track details for a list of track IDs."""
        async with spotify_shared_semaphore:
            try:
                response = await asyncio.to_thread(
                    spotify_user_access.tracks, 
                    track_ids
                )
                return response.get("tracks", []) if response else []
            except Exception as e:
                print(f"Error fetching track details: {e}")
                return []

    RECCO_BATCH_SIZE = 100
    async def add_related_tracks(source_tracks: List[Dict[str, Any]], limit: int):
        """Adds related tracks for a given track list."""
        seed_batches = []
        current_seeds = []
        remaining_limit = limit

        # Generate seed batches
        for track in source_tracks:
            if remaining_limit <= 0:
                break
                
            track_id = track.get("id")
            if not track_id:
                continue

            async with seed_lock:
                if track_id in recco_track_seeds:
                    continue
                recco_track_seeds.add(track_id)
                current_seeds.append(track_id)

            SEED_LIMIT = 5
            if len(current_seeds) == SEED_LIMIT:
                seed_batches.append((current_seeds, min(RECCO_BATCH_SIZE, remaining_limit)))
                current_seeds = []
                remaining_limit -= RECCO_BATCH_SIZE

        # Process leftover seeds if any
        if current_seeds and remaining_limit > 0:
            seed_batches.append((current_seeds, min(RECCO_BATCH_SIZE, remaining_limit)))

        # Get recommendations for all seed batches
        recommendation_coros = [
            recco_beats.get_track_reccomendations(seeds, target_features, batch_limit)
            for seeds, batch_limit in seed_batches
        ]
        recommended_tracks = []
        for batch in await asyncio.gather(*recommendation_coros):
            recommended_tracks.extend(batch)

        # Extract IDs from recommended tracks and filter duplicates
        tracks_to_fetch = []
        async with known_track_lock:
            for track in recommended_tracks:
                href = track.get("href")
                if not href:
                    continue
                track_id = href.split("/")[-1]
                if track_id not in known_track_ids:
                    known_track_ids.add(track_id)
                    tracks_to_fetch.append(track)

        # Batch track details fetching by TRACK_CHUNK_SIZE
        TRACK_CHUNK_SIZE = 50
        track_chunk_details = []
        while tracks_to_fetch:
            chunk = tracks_to_fetch[:TRACK_CHUNK_SIZE]
            del tracks_to_fetch[:TRACK_CHUNK_SIZE]
            
            # Fetch details for this chunk
            details = await fetch_track_details([t["href"] for t in chunk])
            track_chunk_details.extend(details)
        
        # Add to master list with thread safety
        async with track_list_lock:
            track_master_list.extend(track_chunk_details)

    def process_source_tracks(fetch_func: Callable[..., List[Dict[str, Any]]], *args, **kwargs) -> asyncio.Task:
        """
        Creates a task to fetch tracks from a source, add them to a master list,
        and find related tracks. The fetch function is run in a separate thread.

        'related_tracks_limit' must be provided as a keyword argument.
        """
        related_tracks_limit = kwargs.pop("related_tracks_limit")

        async def worker():
            """The actual async work for fetching and processing tracks."""
            # Execute the provided blocking function in a separate thread
            tracks = await asyncio.to_thread(fetch_func, *args, **kwargs)

            # Add source tracks to master list and known IDs
            async with track_list_lock, known_track_lock:
                track_master_list.extend(tracks)
                for track in tracks:
                    if track_id := track.get("id"):
                        known_track_ids.add(track_id)

            # Immediately start processing related tracks
            await add_related_tracks(tracks, related_tracks_limit)
            return tracks

        return asyncio.create_task(worker())

    # Create and manage concurrent tasks
    print("Fetching track sources and processing related tracks...")
    medium_term_task = process_source_tracks(
        spotify_api.get_top_tracks,
        spotify_user_access,
        limit=100,
        time_range="medium_term",
        related_tracks_limit=100,
    )
    short_term_task = process_source_tracks(
        spotify_api.get_top_tracks,
        spotify_user_access,
        limit=100,
        time_range="short_term",
        related_tracks_limit=100,
    )
    saved_tracks_task = process_source_tracks(
        spotify_api.get_saved_tracks,
        spotify_user_access,
        limit=100,
        related_tracks_limit=100,
    )

    # Wait for all tasks to complete
    await asyncio.gather(medium_term_task, short_term_task, saved_tracks_task)

    async def add_relevant_playlist_tracks(playlist_limit: int):
        query = "Upbeat Workout"
        playlists = spotify_api.search_playlist(spotify_user_access, query, 10)
        for playlist in playlists[:min(playlist_limit, len(playlists))]:
            async with spotify_shared_semaphore:
                response = await asyncio.to_thread(spotify_user_access.playlist_items, playlist["id"])
                async with track_list_lock:
                    track_master_list.extend([item["track"] for item in response["items"]])
    
    await add_relevant_playlist_tracks(playlist_limit=5)

    # Deduplicate and return results
    track_master_list = spotify_api.deduplicate_tracks(track_master_list)
    print(f"Final track count: {len(track_master_list)}")
    print("Sample tracks:", [track["name"] for track in track_master_list[:100]])

    return {"track_master_list": track_master_list}, {"message": ""}


def analyze_mood(dependencies: dict) -> Tuple[dict, dict]:
    """Simulate CPU-intensive mood analysis"""
    time.sleep(3)
    internal = {"mood_score": 0.85, "valence": 0.7, "arousal": 0.6}
    client = {"message": "Detected positive mood with high energy"}
    return internal, client

async def build_feature_matrix(dependencies: dict) -> Tuple[dict, dict]:
    """Simulate async feature processing"""
    await asyncio.sleep(2)
    internal = {"matrix": [[0.1, 0.4], [0.2, 0.5]], "features": 300}
    client = {"message": "Processed 500 songs with 30 acoustic features each"}
    return internal, client

def run_kd_tree(dependencies: dict) -> Tuple[dict, dict]:
    """Simulate algorithm execution using dependencies"""
    mood = dependencies["mood_analysis"]
    features = dependencies["feature_matrix"]
    time.sleep(4)
    internal = {
        "tree_depth": 15,
        "nearest_neighbors": 50,
        "mood_params": mood["mood_score"]
    }
    client = {
        "message": f"Matched songs using mood profile ({mood['mood_score']})",
        "stats": f"{len(features['matrix'])}x{features['features']} matrix"
    }
    return internal, client

def compile_results(dependencies: dict) -> Tuple[dict, dict]:
    """Simulate result compilation using dependencies"""
    kd_tree = dependencies["kd_tree"]
    time.sleep(1)
    internal = {"playlist_ids": [1, 5, 12, 45, 23]}
    client = {
        "message": "Your perfect playlist is ready!",
        "songs": 5,
        "duration": "15:42"
    }
    return internal, client

# Task configuration with execution functions
TASK_DEFINITIONS = [
    {
        "id": "compile_track_list",
        "label": "Compiling Potential Tracks",
        "description": "[todo]",
        "function": compile_track_list_task,
        "dependencies": []
    },
    {
        "id": "mood_analysis",
        "label": "Analyzing mood parameters",
        "description": "Processing emotional cues to determine musical preferences",
        "function": analyze_mood,
        "dependencies": [],
    },
    {
        "id": "feature_matrix",
        "label": "Building song feature matrix",
        "description": "Extracting and organizing acoustic features from library",
        "function": build_feature_matrix,
        "dependencies": [],
    },
    {
        "id": "kd_tree",
        "label": "Running KD-Tree algorithm",
        "description": "Optimizing song search using spatial partitioning",
        "function": run_kd_tree,
        "dependencies": ["mood_analysis", "feature_matrix"],
    },
    {
        "id": "result_compilation",
        "label": "Compiling results",
        "description": "Assembling final playlist recommendations",
        "function": compile_results,
        "dependencies": ["kd_tree"],
    }
]

def topological_sort(tasks: List[dict]) -> List[List[dict]]:
    """Group tasks into parallelizable stages based on dependencies"""
    task_map: dict[str, dict] = {t["id"]: t for t in tasks}

    stages: List[List[dict]] = []

    remaining_tasks: set[str] = set([t["id"] for t in tasks])
    ready_tasks: set[str] = set()

    while(remaining_tasks):
        next_remaining: set[str] = remaining_tasks.copy()
        next_ready: set[str] = set()
        
        for id in remaining_tasks:
            indeg = len([dep for dep in task_map[id]["dependencies"] if dep in remaining_tasks])
            if indeg == 0:
                next_remaining.remove(id)
                next_ready.add(id)
        
        remaining_tasks = next_remaining
        ready_tasks = next_ready
        
        if ready_tasks:
            stages.append([task_map[id] for id in ready_tasks])
        else:
            break
    
    return stages
# Group tasks into parallel execution stages
task_stages = topological_sort(TASK_DEFINITIONS)
print ("Task Stages:\n\t", '\n\t'.join([", ".join([task["id"] for task in stage]) for stage in task_stages]))

async def task_generator(request: Request | None, spotify_user_access: Spotify, favorite_songs: list[str] | None):
    """Generates streaming updates for playlist generation"""

    # Store dependency results for passing to tasks
    all_results = {
        "spotify_user_access": spotify_user_access,
        "favorite_songs": favorite_songs
    }

    # Send initial task definitions and state
    initial_state = {
        "type": "initial",
        "timestamp": time.time(),
        "tasks": [
            {
                "id": task["id"],
                "label": task["label"],
                "description": task["description"],
                "status": "pending",
            }
            for task in TASK_DEFINITIONS
        ],
    }
    yield json.dumps(initial_state) + "\n\n"

        # Create thread pool for synchronous tasks
    with concurrent.futures.ThreadPoolExecutor() as pool:
        # Process tasks in stages
        for stage in task_stages:
            # Check client connection
            if request is not None and await request.is_disconnected():
                return

            # Create a queue for updates from this stage
            update_queue = asyncio.Queue()
            
            # Create tasks for all tasks in this stage
            tasks = []
            for task in stage:
                # Create a task that processes all updates for this task
                async def run_task(task):
                    async for update in execute_task(task, pool, all_results):
                        await update_queue.put(update)
                tasks.append(asyncio.create_task(run_task(task)))

            # Process updates as they arrive
            while tasks:
                # Check client connection
                if request is not None and await request.is_disconnected():
                    for task in tasks:
                        task.cancel()
                    return
                
                # Wait for next update or task completion
                done, pending = await asyncio.wait(
                    [*tasks, asyncio.create_task(update_queue.get())],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process updates
                for future in done:
                    try: 
                        if future in tasks:
                            # Task completed - remove it
                            tasks.remove(future)
                            continue
                        
                        # This is an update from the queue
                        update = future.result()
                        yield update
                        
                        # Immediately check for disconnection
                        if request is not None and await request.is_disconnected():
                            for task in tasks:
                                task.cancel()
                            return
                    except Exception as e:
                        yield json.dumps({
                            "type": "error",
                            "error": str(e),
                            "timestamp": time.time()
                        }) + "\n\n"

    # Final completion
    yield json.dumps({
        "type": "final",
        "timestamp": time.time(),
        "playlist_id": ""
    }) + "\n\n"


async def execute_task(task, pool, all_results):
    """Execute task and yield updates (now as async generator)"""
    task_id = task["id"]

    # Send task running update to client
    update = {
        "type": "update",
        "timestamp": time.time(),
        "task_id": task_id,
        "status": "running"
    }
    yield json.dumps(update) + "\n\n"

    start_time = time.perf_counter_ns()
    try:
        # Execute task function
        if asyncio.iscoroutinefunction(task["function"]):
            result = await task["function"](all_results)
        else:
            # Run synchronous function in thread pool
            result = await asyncio.get_running_loop().run_in_executor(
                pool,
                lambda: task["function"](all_results)
            )

        duration_ns = time.perf_counter_ns() - start_time

        # Handle return values
        internal_results = None
        client_results = None
        if isinstance(result, tuple) and len(result) == 2:
            internal_results, client_results = result
        else:
            internal_results = result

        # Store results for dependencies
        all_results[task_id] = internal_results

        # Send update to client
        update = {
            "type": "update",
            "timestamp": time.time(),
            "task_id": task_id,
            "status": "completed",
            "duration": f"{(duration_ns/1_000_000):.0f}ms"
        }
        if client_results is not None:
            update["data"] = client_results
        yield json.dumps(update) + "\n\n"
    except Exception as e:
        duration_ns = time.perf_counter_ns() - start_time
        yield json.dumps({
            "type": "update",
            "timestamp": time.time(),
            "task_id": task_id,
            "status": "failed",
            "duration": f"{(duration_ns/1_000_000):.0f}ms",
            "error": str(e)
        }) + "\n\n"

async def test_task(task, dependencies: dict = {}):
    from spotify_auth import initialize_algorithms_account, algorhythms_account
    initialize_algorithms_account()

    if(not dependencies.get("spotify_user_access")):
        dependencies["spotify_user_access"] = algorhythms_account
    if(not dependencies.get("favorite_songs")):
        dependencies["favorite_songs"] = []
    
    start_time = time.perf_counter_ns()
    internal, client = await task(dependencies)
    duration_ns = time.perf_counter_ns() - start_time
    print ("Duration: ", f"{(duration_ns/1_000_000):.0f}ms")

    # print("Internal", internal)
    # print("Client", client)

async def main():
    """Asynchronous main testing function to run the generator."""
    from spotify_auth import initialize_algorithms_account, algorhythms_account
    initialize_algorithms_account()
    print("--- Starting Playlist Generation ---")
    async for value in task_generator(None, algorhythms_account, None):
        print(value)
    print("--- Playlist Generation Complete ---")

if __name__ == "__main__":
    asyncio.run(test_task(compile_track_list_task))