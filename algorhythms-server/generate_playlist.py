"""
A dynamic, concurrent task execution engine for generating Spotify playlists.

This script defines a system for running a dependency graph of tasks, some of which
can be long-running and yield intermediate progress updates. It is designed to be
both efficient, by running tasks concurrently as soon as their dependencies are met,
and maintainable, through clear separation of concerns, strong typing, and
comprehensive documentation.
"""
import asyncio
import inspect
import json
import time
from typing import Dict, Literal, Tuple, Any, AsyncGenerator, Awaitable, Callable, Dict, List, Optional, Set, Tuple
import concurrent.futures
from fastapi import Request
from pydantic import BaseModel
from _types import *
from spotipy import Spotify

class TaskID(NamedStringType):
    pass

InternalResult = Dict[str, Any]
ClientResult = Dict[str, Any]
TaskResult = Tuple[InternalResult, ClientResult]

class ProgressUpdate(Dict[str, Any]):
    pass
GeneratorResults = AsyncGenerator[ProgressUpdate]
ResultCallback = Callable[[TaskResult],  None]

DependencyDict = Dict[str, Any]
TaskFunction = Callable[[DependencyDict, ResultCallback], GeneratorResults] | Callable[[DependencyDict], Awaitable[TaskResult]]

class Task(BaseModel):
    """Defines a single task, automatically inferring its execution style."""
    id: TaskID
    label: str
    description: str
    function: TaskFunction
    dependencies: List[TaskID]

# Task Definitions

async def compile_track_list_task(deps: DependencyDict) -> TaskResult:
    # Example usage: spotify = deps["spotify_user_access"]
    await asyncio.sleep(1)
    return {"track_list": 100}, {"message": "Tracks compiled successfully"}

async def process_audio_task(deps: DependencyDict, result: ResultCallback) -> GeneratorResults:
    # Actual implementation would go here
    steps = 3
    for i in range(steps):
        # Simulate processing time
        await asyncio.sleep(1)
        # Yield progress update
        yield ProgressUpdate({"message": f"Processed {i+1}/{steps} audio segments"})
    
    # Return final result
    result(({}, {"message": "Audio processing complete"}))

_seen_task_ids: Set[TaskID] = set()
def define_task(**data: Any) -> Task:
    id = data.get("id", None)
    task_id = TaskID(id)
    _seen_task_ids.add(task_id)

    dependencies = data.get("dependencies", [])
    dep_ids = [TaskID(dep_id) for dep_id in dependencies]
    for dep_id in dep_ids:
        if(dep_id not in _seen_task_ids):
            raise ValueError(f"Task with ID: {task_id} depends on task with ID {dep_id} which has not been defined yet")

    return Task(**data)

TASK_DEFINITIONS: List[Task] = [
    define_task(
        id="compile_track_list", 
        label="Compiling Tracks", 
        description="...",
        function=compile_track_list_task, 
        dependencies=[]
    ),
    define_task(
        id="process_audio", 
        label="Processing Audio", 
        description="...",
        function=process_audio_task, 
        dependencies=["compile_track_list"]
    )
]


class TaskRunner:
    """Manages the dynamic execution of a graph of tasks."""

    def __init__(self, tasks: List[Task], initial_deps: Dict[str, Any]) -> None:
        self.tasks_by_id: Dict[TaskID, Task] = {t.id: t for t in tasks}
        self.initial_deps: Dict[str, Any] = initial_deps
        
        self.completed_tasks: Set[TaskID] = set()
        self.failed_tasks: Set[TaskID] = set()
        self.internal_task_results: Dict[TaskID, InternalResult] = {}
        self.running_tasks: Dict[TaskID, asyncio.Task] = {}
        
        # Concurrency and signaling
        self.task_update_queue = asyncio.Queue()
        self.abort_event = asyncio.Event()

    def _format_update(self, task_id: TaskID, status: Literal["running", "progress", "failed", "completed"], data=None, error=None, duration=None):
        update = {
            "type": "update",
            "timestamp": time.time(),
            "task_id": task_id,
            "status": status,
        }
        if data: update["data"] = data
        if error: update["error"] = error
        if duration is not None: update["duration"] = f"{duration:.0f}ms"
        return json.dumps(update) + "\n\n"

    def _task_done_callback(self, task: asyncio.Task, task_id: TaskID):
        """Callback run when a task finishes, fails, or is cancelled."""
        # Remove from running tasks
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]

        # If the task failed with an unhandled exception, abort the entire run.
        if not task.cancelled() and task.exception():
            print(f"Task {task_id} failed with an unhandled exception: {task.exception()}")
            self.abort_event.set()

    async def _execute_task(self, task: Task):
        """Runs a single task and puts all its updates onto the shared queue."""
        start_time = time.perf_counter_ns()
        deps: Dict[str, Any] = self.initial_deps.copy()
        for dep_id in task.dependencies:
            deps.update(self.internal_task_results.get(dep_id, {}))
        
        try:
            await self.task_update_queue.put(self._format_update(task.id, status="running"))
            
            final_result: Optional[TaskResult] = None
            if inspect.isasyncgenfunction(task.function):

                def result_callback(result: TaskResult):
                    nonlocal final_result
                    final_result = result

                task_gen = task.function(deps, result_callback)
                async for progress in task_gen:
                    await self.task_update_queue.put(self._format_update(task.id, "progress", data=progress))
                    if final_result:
                        break
            elif inspect.iscoroutinefunction(task.function):
                final_result = await task.function(deps)

            if not final_result:
                raise ValueError(f"Task {task.id} did not produce a final result.")

            internal_result, client_result = final_result
            self.internal_task_results[task.id] = internal_result
            self.completed_tasks.add(task.id)
            duration = (time.perf_counter_ns() - start_time) / 1_000_000
            await self.task_update_queue.put(self._format_update(
                task.id, "completed", data=client_result, duration=duration
            ))
        except asyncio.CancelledError:
            await self.task_update_queue.put(self._format_update(task.id, "failed", error="Task was cancelled."))
            raise
        except Exception as e:
            duration = (time.perf_counter_ns() - start_time) / 1_000_000
            self.failed_tasks.add(task.id) # Mark as failed, NOT completed.
            await self.task_update_queue.put(self._format_update(
                task.id, "failed", error=str(e), duration=duration
            ))
            raise # The exception is passed to the done_callback.

    async def _cancel_all_running_tasks(self):
        """Cancels all tasks currently in self.running_tasks."""
        if not self.running_tasks:
            return
        
        for task in self.running_tasks.values():
            task.cancel()
        
        # Wait for all cancellations to be processed
        await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)

    async def run_generator(self, request_client: Optional[Request]):
        """Main async generator that yields formatted JSON updates to the client."""
        pending_task_ids = set(self.tasks_by_id.keys())

        try:
            while pending_task_ids or self.running_tasks:
                if self.abort_event.is_set() or (request_client and await request_client.is_disconnected()):
                    await self._cancel_all_running_tasks()
                    break

                # Schedule newly ready tasks
                ready_task_ids = {
                    task_id for task_id in pending_task_ids
                    if all(dep_id in self.completed_tasks for dep_id in self.tasks_by_id[task_id].dependencies)
                }

                for task_id in ready_task_ids:
                    task_instance = self.tasks_by_id[task_id]
                    task = asyncio.create_task(self._execute_task(task_instance))
                    self.running_tasks[task_id] = task
                    task.add_done_callback(lambda t, tid=task_id: self._task_done_callback(t, tid))
                
                pending_task_ids -= ready_task_ids

                # Check for deadlocks
                if not self.running_tasks and pending_task_ids:
                    raise ValueError(f"Deadlock detected. Pending tasks: {pending_task_ids}")

                # Efficiently wait for the next event to happen
                queue_getter = asyncio.create_task(self.task_update_queue.get())
                abort_waiter = asyncio.create_task(self.abort_event.wait())
                
                done, pending = await asyncio.wait(
                    [queue_getter, abort_waiter], return_when=asyncio.FIRST_COMPLETED
                )

                if queue_getter in done:
                    abort_waiter.cancel()
                    yield queue_getter.result()
                
                if abort_waiter in done:
                    queue_getter.cancel()
                    # Abort event was set, loop will be broken on next iteration
                    continue
            
            # Drain any remaining updates from the queue
            while not self.task_update_queue.empty():
                yield self.task_update_queue.get_nowait()
                
        finally:
            # Ensure all tasks are cancelled on exit
            await self._cancel_all_running_tasks()

async def playlist_task_generator(
        request: Optional[Request],
        spotify_user_access: Spotify
):
    '''Main API entrypoint that creates and runs the TaskRunner.'''
    initial_deps = {"spotify_user_access": spotify_user_access}
    runner = TaskRunner(TASK_DEFINITIONS, initial_deps)
    try:
        async for update in runner.run_generator(request):
            yield update
    except Exception as e:
        # Yield a final error message if the runner itself fails
        error_payload = {"type": "error", "message": f"Task runner failed: str{e}"}
        yield json.dumps(error_payload) + "\n\n"
    finally:
        yield json.dumps({"type": "final", "timestamp": time.time()}) + "\n\n"

async def main():
    """An asynchronous main function to run the full generator for standalone testing."""
    from spotify_auth import get_spotify_clients
    _, algorhythms_account = await get_spotify_clients()
    
    print("--- Starting Dynamic Playlist Generation Test ---")
    async for value in playlist_task_generator(None, algorhythms_account):
        print(value, end="")
    print("\n--- Playlist Generation Complete ---")

if __name__ == "__main__":
    asyncio.run(main())