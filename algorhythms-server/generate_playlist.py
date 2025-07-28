import asyncio
import json
import time
from typing import Any, List, Set, Tuple
import concurrent.futures
from fastapi import Request
import spotify_api
import recco_beats
from spotipy import Spotify

# Define task functions with dependency handling
async def compile_track_list(dependencies: dict) -> Tuple[dict, dict]:
    spotify_user_access = dependencies["spotify_user_access"]
    track_master_list = []

    top_tracks = spotify_api.get_top_tracks(spotify_user_access, 100, "medium_term")
    track_master_list.extend(top_tracks)

    top_tracks_recent = spotify_api.get_top_tracks(spotify_user_access, 100, "short_term")
    track_master_list.extend(top_tracks_recent)

    saved_tracks = spotify_api.get_saved_tracks(spotify_user_access, 100)
    track_master_list.extend(saved_tracks)

    target_features: recco_beats.TargetFeatures = {
        # "instrumentalness": 0.8,
        # "energy": 0.2,
        # "speechiness": 0.1,
        # "tempo": 80,
    }

    # This semaphore is shared across all calls to add_related_tracks,
    # limiting the total number of concurrent Spotify API calls to 10.
    shared_semaphore = asyncio.Semaphore(10)
    
    # These are also shared across all calls.
    recco_track_seeds: Set[str] = set()

    async def add_related_tracks(tracks: List[dict[str, Any]], limit: int):
        page_seed_ids = []
        i = 0

        seed_ids: list[str] = []
        while(limit > 0 and i < len(tracks)):
            track_id = tracks[i].get("id")
            i += 1
            if track_id and track_id not in recco_track_seeds:
                recco_track_seeds.add(track_id)
                seed_ids.append(track_id)
                if len(seed_ids) == 5: # 1. Select up to 5 unique seed tracks.
                    _limit = min(100, limit)
                    page_seed_ids.append((_limit, seed_ids))
                    seed_ids = []
                    limit -= 100

        # 2. Get recommendations based on the seeds.
        fetch_recommended_tracks_tasks = [recco_beats.get_track_reccomendations(_seed_ids, target_features, _limit) for _limit, _seed_ids in page_seed_ids]
        page_recommended_tracks = await asyncio.gather(*fetch_recommended_tracks_tasks)
        recommended_tracks = [track for sublist in page_recommended_tracks for track in sublist]

        # 3. Chunk the recommended tracks into groups of 50 (the Spotify API limit).
        chunk_size = 50
        track_chunks = [
            recommended_tracks[i:i + chunk_size] 
            for i in range(0, len(recommended_tracks), chunk_size)
        ]

        # 4. Define a coroutine to fetch one chunk, respecting the semaphore.
        async def fetch_track_chunk(chunk):
            async with shared_semaphore:
                try:
                    # The API call is for a chunk of up to 50 tracks.
                    track_ids = [track["href"] for track in chunk]
                    response = await asyncio.to_thread(spotify_user_access.tracks, track_ids)
                    
                    # The response contains a list of tracks, so use extend.
                    if response and response.get("tracks"):
                        track_master_list.extend(response["tracks"])
                except Exception as e:
                    print(f"Error fetching track chunk: {e}")

        # 5. Create and run concurrent tasks for each chunk.
        fetch_tasks = [fetch_track_chunk(chunk) for chunk in track_chunks]
        await asyncio.gather(*fetch_tasks)


    # --- Execution ---
    print("Adding related tracks...")
    
    # All three calls to add_related_tracks will run concurrently.
    # They will all use the exact same `shared_semaphore`.
    await asyncio.gather(
        add_related_tracks(top_tracks, 200),
        add_related_tracks(top_tracks_recent, 200),
        add_related_tracks(saved_tracks, 200),
    )


    track_master_list = spotify_api.deduplicate_tracks(track_master_list)
    print("deduped: ", len(track_master_list))
    print([track["name"] for track in track_master_list][:100])

    internal = {"track_master_list": track_master_list}
    client = {"message": ""}
    return internal, client

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
        "function": compile_track_list,
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
    asyncio.run(test_task(compile_track_list))