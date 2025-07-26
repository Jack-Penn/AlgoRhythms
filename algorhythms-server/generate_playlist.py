import asyncio
import json
import time
from typing import List, Tuple
import concurrent.futures
from fastapi import Request

# Define task functions with dependency handling
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



async def task_generator(request: Request | None):
    """Generates streaming updates for playlist generation"""
    # Group tasks into parallel execution stages
    task_stages = topological_sort(TASK_DEFINITIONS)
    print (task_stages)
    # Store dependency results for passing to tasks
    all_results = {}

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

async def main():
    """Asynchronous main testing function to run the generator."""
    print("--- Starting Playlist Generation ---")
    async for value in task_generator(None):
        print(value)
    print("--- Playlist Generation Complete ---")

if __name__ == "__main__":
    asyncio.run(main())