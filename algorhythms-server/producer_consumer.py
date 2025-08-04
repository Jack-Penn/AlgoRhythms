import asyncio
from typing import Any, Awaitable, Callable, Coroutine, Generic, List, Optional, TypeVar

ItemType = TypeVar('ItemType')
ProduceBatchCallback = Callable[[], Coroutine[Any, Any, None]]
ConsumeBatchCallback = Callable[[List[ItemType]], Awaitable[None]]

class ProducerConsumer(Generic[ItemType]):
    def __init__(self, consumer_callback: ConsumeBatchCallback, batch_size: int = 1):
        self.shared_queue: asyncio.Queue[Optional[ItemType]] = asyncio.Queue()
        self.consumer_callback = consumer_callback
        self.batch_size = batch_size
        
        self.consumer_task: Optional[asyncio.Task] = None
        self.producer_tasks: List[asyncio.Task] = []
        self._lock = asyncio.Lock()
        self._is_started = False

    async def append_item(self, item: ItemType) -> None:
        await self.shared_queue.put(item)

    async def add_producers(self, producer_callbacks: List[ProduceBatchCallback]):
        async with self._lock:
            if not self._is_started:
                print(f"Warning: Producers added before service for {self.consumer_callback.__name__} was started.")
                return
            for callback in producer_callbacks:
                task = asyncio.create_task(callback())
                self.producer_tasks.append(task)
    
    async def _consumer(self):
        items_buffer: List[ItemType] = []
        while True:
            try:
                item = await self.shared_queue.get()

                # Sentinel value (None) means shutdown
                if item is None:
                    self.shared_queue.task_done()
                    break 

                items_buffer.append(item)
                
                if len(items_buffer) >= self.batch_size:
                    await self.consumer_callback(items_buffer)
                    items_buffer.clear()
                
                self.shared_queue.task_done()
            except Exception as e:
                import traceback
                print(f"Error in consumer {self.consumer_callback.__name__} while processing batch. Error: {e}")
                traceback.print_exc()
                # Breaking here stops the consumer on any error.
                break
        
        # After the loop breaks, process any remaining items in the buffer.
        if items_buffer:
            print(f"Consumer for {self.consumer_callback.__name__} processing final batch...")
            try:
                await self.consumer_callback(items_buffer)
            except Exception as e:
                import traceback
                print(f"Error in consumer {self.consumer_callback.__name__} during final batch. Error: {e}")
                traceback.print_exc()
    
    async def start(self):
        """Starts the consumer task, making the service ready to accept items."""
        async with self._lock:
            if self._is_started:
                return
            self.consumer_task = asyncio.create_task(self._consumer())
            self._is_started = True
            print(f"ProducerConsumer service for {self.consumer_callback.__name__} started.")

    async def finish(self):
        """Waits for producers to finish, then gracefully stops the consumer."""
        # Wait for all producer tasks to complete.
        if self.producer_tasks:
            await asyncio.gather(*self.producer_tasks, return_exceptions=True)
        
        # Send the sentinel value to the queue to signal the consumer to stop.
        await self.shared_queue.put(None)
        
        # Wait for the consumer task to finish processing everything.
        if self.consumer_task:
            await self.consumer_task
        
        print(f"ProducerConsumer service for {self.consumer_callback.__name__} has finished.")