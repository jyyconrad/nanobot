"""Async task scheduler with priority and resource management."""

import asyncio
import heapq
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from loguru import logger


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class ScheduledTask:
    """Represents a scheduled task with priority."""
    priority: TaskPriority
    task_id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    submit_time: float = field(default_factory=time.time)
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3

    def __lt__(self, other):
        """Compare tasks for priority queue."""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.submit_time < other.submit_time


class TaskScheduler:
    """
    Async task scheduler with priority queues and resource management.

    Features:
    - Priority-based task scheduling
    - Resource pool management
    - Task retry with exponential backoff
    - Performance monitoring
    - Load balancing
    """

    def __init__(
        self,
        max_workers: int = 10,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        timeout: float = 300.0
    ):
        """
        Initialize task scheduler.

        Args:
            max_workers: Maximum concurrent workers
            max_retries: Default max retry attempts
            backoff_factor: Exponential backoff multiplier
            timeout: Default task timeout (seconds)
        """
        self.max_workers = max_workers
        self.default_max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.default_timeout = timeout

        self._priority_queue: List[Tuple[int, ScheduledTask]] = []
        self._queue_lock = asyncio.Lock()
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        self._results: Dict[str, Any] = {}
        self._errors: Dict[str, str] = {}
        self._completion_events: Dict[str, asyncio.Event] = {}

        # Performance metrics
        self._task_stats: Dict[str, Dict] = {}

    async def start(self):
        """Start the scheduler."""
        if self._running:
            logger.warning("Task scheduler already running")
            return

        self._running = True
        logger.info(f"Starting task scheduler with {self.max_workers} workers")

        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._worker_tasks.append(worker)

    async def stop(self):
        """Stop the scheduler."""
        if not self._running:
            return

        logger.info("Stopping task scheduler")
        self._running = False

        # Cancel worker tasks
        for worker in self._worker_tasks:
            worker.cancel()

        # Wait for workers
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

        logger.info("Task scheduler stopped")

    async def schedule(
        self,
        task_id: str,
        name: str,
        func: Callable,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        **kwargs
    ) -> None:
        """
        Schedule a task for execution.

        Args:
            task_id: Unique task identifier
            name: Human-readable task name
            func: Async function to execute
            *args: Positional arguments
            priority: Task priority
            timeout: Task timeout
            max_retries: Maximum retry attempts
            **kwargs: Keyword arguments
        """
        task = ScheduledTask(
            priority=priority,
            task_id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            timeout=timeout or self.default_timeout,
            max_retries=max_retries or self.default_max_retries
        )

        async with self._queue_lock:
            heapq.heappush(self._priority_queue, (task.priority.value, task))
            self._completion_events[task_id] = asyncio.Event()

        logger.info(f"Task scheduled: {task_id} - {name} (priority={priority.name})")

    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Wait for a task to complete.

        Args:
            task_id: Task ID
            timeout: Wait timeout

        Returns:
            Task result

        Raises:
            TimeoutError: If timeout exceeded
            RuntimeError: If task failed
        """
        event = self._completion_events.get(task_id)
        if not event:
            raise RuntimeError(f"Task not found: {task_id}")

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Wait timeout for task: {task_id}")

        # Check for errors
        if task_id in self._errors:
            raise RuntimeError(self._errors[task_id])

        return self._results.get(task_id)

    async def _worker(self, worker_name: str):
        """
        Worker coroutine.

        Args:
            worker_name: Worker identifier
        """
        logger.info(f"{worker_name} started")

        while self._running:
            try:
                # Get next task
                task = await self._get_next_task()
                if not task:
                    await asyncio.sleep(0.1)
                    continue

                logger.info(f"{worker_name} executing: {task.task_id}")

                # Execute task
                try:
                    start_time = time.time()
                    result = await asyncio.wait_for(
                        task.func(*task.args, **task.kwargs),
                        timeout=task.timeout
                    )
                    execution_time = time.time() - start_time

                    # Store result
                    self._results[task.task_id] = result
                    self._record_success(task.task_id, execution_time)

                    logger.info(f"{worker_name} completed: {task.task_id} in {execution_time:.2f}s")

                except asyncio.TimeoutError:
                    error_msg = f"Task timeout after {task.timeout}s"

                    # Check if we should retry
                    task.retry_count += 1
                    if task.retry_count < task.max_retries:
                        delay = self.backoff_factor ** task.retry_count
                        logger.info(f"Retrying {task.task_id} (attempt {task.retry_count + 1}/{task.max_retries}) after {delay}s")
                        await asyncio.sleep(delay)
                        async with self._queue_lock:
                            heapq.heappush(self._priority_queue, (task.priority.value, task))
                    else:
                        # Final failure
                        self._errors[task.task_id] = error_msg
                        self._record_failure(task.task_id, error_msg)
                        logger.error(f"{worker_name} task timeout (final): {task.task_id}")

                except Exception as e:
                    error_msg = str(e)

                    # Check if we should retry
                    task.retry_count += 1
                    if task.retry_count < task.max_retries:
                        delay = self.backoff_factor ** task.retry_count
                        logger.info(f"Retrying {task.task_id} (attempt {task.retry_count + 1}/{task.max_retries}) after {delay}s")
                        await asyncio.sleep(delay)
                        async with self._queue_lock:
                            heapq.heappush(self._priority_queue, (task.priority.value, task))
                    else:
                        # Final failure
                        self._errors[task.task_id] = error_msg
                        self._record_failure(task.task_id, error_msg)
                        logger.error(f"{worker_name} task error (final): {task.task_id} - {error_msg}")

                finally:
                    # Signal completion
                    event = self._completion_events.get(task.task_id)
                    if event:
                        event.set()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{worker_name} error: {e}")
                await asyncio.sleep(0.1)

        logger.info(f"{worker_name} stopped")

    async def _get_next_task(self) -> Optional[ScheduledTask]:
        """Get the next task from the priority queue."""
        async with self._queue_lock:
            if not self._priority_queue:
                return None

            _, task = heapq.heappop(self._priority_queue)
            return task

    async def _handle_failure(self, task: ScheduledTask, error_msg: str):
        """Handle task failure: record attempt. Task is already failed by worker."""
        task.retry_count += 1
        self._errors[task.task_id] = error_msg
        self._record_failure(task.task_id, error_msg)

    def _record_success(self, task_id: str, execution_time: float):
        """Record successful task execution."""
        if task_id not in self._task_stats:
            self._task_stats[task_id] = {
                "attempts": 0,
                "successes": 0,
                "failures": 0,
                "total_time": 0.0
            }

        self._task_stats[task_id]["attempts"] += 1
        self._task_stats[task_id]["successes"] += 1
        self._task_stats[task_id]["total_time"] += execution_time

    def _record_failure(self, task_id: str, error_msg: str):
        """Record task failure."""
        if task_id not in self._task_stats:
            self._task_stats[task_id] = {
                "attempts": 0,
                "successes": 0,
                "failures": 0,
                "total_time": 0.0,
                "errors": []
            }

        self._task_stats[task_id]["attempts"] += 1
        self._task_stats[task_id]["failures"] += 1

        if "errors" not in self._task_stats[task_id]:
            self._task_stats[task_id]["errors"] = []

        self._task_stats[task_id]["errors"].append(error_msg)

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        stats = {
            "is_running": self._running,
            "max_workers": self.max_workers,
            "queue_size": len(self._priority_queue),
            "completed_tasks": len(self._results),
            "failed_tasks": len(self._errors),
        }

        # Calculate success rate
        total_completed = len(self._results) + len(self._errors)
        if total_completed > 0:
            stats["success_rate"] = len(self._results) / total_completed
        else:
            stats["success_rate"] = 0.0

        return stats

    def get_task_stats(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific task."""
        return self._task_stats.get(task_id)


class ResourcePool:
    """
    Resource pool for managing limited resources like API rate limits,
    database connections, etc.
    """

    def __init__(self, max_size: int, acquire_timeout: float = 30.0):
        """
        Initialize resource pool.

        Args:
            max_size: Maximum pool size
            acquire_timeout: Timeout for acquiring a resource
        """
        self.max_size = max_size
        self.acquire_timeout = acquire_timeout
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._created = 0
        self._acquired = 0
        self._lock = asyncio.Lock()

    async def initialize(self, creator: Callable):
        """
        Initialize pool with resources.

        Args:
            creator: Async function that creates a resource
        """
        for _ in range(self.max_size):
            resource = await creator()
            await self._pool.put(resource)
            self._created += 1

    async def acquire(self) -> Any:
        """Acquire a resource from the pool."""
        try:
            resource = await asyncio.wait_for(
                self._pool.get(),
                timeout=self.acquire_timeout
            )
            async with self._lock:
                self._acquired += 1
            return resource
        except asyncio.TimeoutError:
            raise TimeoutError(f"Failed to acquire resource within {self.acquire_timeout}s")

    async def release(self, resource: Any):
        """Release a resource back to the pool."""
        await self._pool.put(resource)
        async with self._lock:
            self._acquired -= 1

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            "max_size": self.max_size,
            "created": self._created,
            "acquired": self._acquired,
            "available": self._pool.qsize()
        }
