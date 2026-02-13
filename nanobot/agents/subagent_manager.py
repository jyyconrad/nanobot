"""Subagent management with concurrency control."""

import asyncio
import os
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import psutil
from loguru import logger


class SubagentStatus(Enum):
    """Subagent execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SubagentTask:
    """Represents a subagent task."""

    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    status: SubagentStatus = SubagentStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SubagentManager:
    """
    Manages subagent execution with concurrency control.

    Features:
    - Concurrent subagent execution with semaphore-based limiting
    - Task queuing and scheduling
    - Error handling and recovery
    - Progress tracking
    - Resource management
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        timeout: float = 600.0,
        max_memory_mb: Optional[float] = None,
        max_cpu_percent: float = 90.0,
        cleanup_interval: float = 60.0,
    ):
        """
        Initialize subagent manager.

        Args:
            max_concurrent: Maximum number of concurrent subagents
            timeout: Default timeout for each task (seconds)
            max_memory_mb: Maximum memory usage in MB (None = no limit)
            max_cpu_percent: Maximum CPU usage percentage
            cleanup_interval: Interval for resource cleanup (seconds)
        """
        self.max_concurrent = max_concurrent
        self.default_timeout = timeout
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.cleanup_interval = cleanup_interval

        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._tasks: Dict[str, SubagentTask] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._task_lock = asyncio.Lock()
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []

        # Resource monitoring
        self._process = psutil.Process(os.getpid())
        self._cleanup_task: Optional[asyncio.Task] = None
        self._completed_task_retention = 100  # Keep last 100 completed tasks

    async def start(self):
        """Start the subagent manager worker pool."""
        if self._running:
            logger.warning("Subagent manager already running")
            return

        self._running = True
        logger.info(f"Starting subagent manager with {self.max_concurrent} workers")

        # Start worker tasks
        for i in range(self.max_concurrent):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._worker_tasks.append(worker)

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop the subagent manager."""
        if not self._running:
            return

        logger.info("Stopping subagent manager")
        self._running = False

        # Cancel worker tasks
        for worker in self._worker_tasks:
            worker.cancel()

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

        logger.info("Subagent manager stopped")

    async def submit_task(
        self,
        task_id: str,
        name: str,
        func: Callable,
        *args,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> str:
        """
        Submit a task for execution.

        Args:
            task_id: Unique task identifier
            name: Human-readable task name
            func: Async function to execute
            *args: Positional arguments for func
            timeout: Task timeout (uses default if None)
            **kwargs: Keyword arguments for func

        Returns:
            Task ID
        """
        task = SubagentTask(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            metadata={"timeout": timeout or self.default_timeout},
        )

        async with self._task_lock:
            self._tasks[task_id] = task

        await self._task_queue.put(task)
        logger.info(f"Task submitted: {task_id} - {name}")

        return task_id

    async def get_task(self, task_id: str) -> Optional[SubagentTask]:
        """
        Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task or None if not found
        """
        async with self._task_lock:
            return self._tasks.get(task_id)

    async def get_all_tasks(self) -> List[SubagentTask]:
        """
        Get all tasks.

        Returns:
            List of all tasks
        """
        async with self._task_lock:
            return list(self._tasks.values())

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or running task.

        Args:
            task_id: Task ID

        Returns:
            True if cancelled, False if not found or already completed
        """
        async with self._task_lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            if task.status in (SubagentStatus.PENDING, SubagentStatus.RUNNING):
                task.status = SubagentStatus.CANCELLED
                task.end_time = time.time()
                logger.info(f"Task cancelled: {task_id}")
                return True

            return False

    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Wait for a task to complete.

        Args:
            task_id: Task ID
            timeout: Wait timeout (None = wait indefinitely)

        Returns:
            Task result

        Raises:
            TimeoutError: If timeout exceeded
            RuntimeError: If task failed
        """
        start_time = time.time()
        check_interval = 0.1

        while True:
            task = await self.get_task(task_id)
            if not task:
                raise RuntimeError(f"Task not found: {task_id}")

            if task.status == SubagentStatus.COMPLETED:
                return task.result

            if task.status == SubagentStatus.FAILED:
                raise RuntimeError(f"Task failed: {task.error}")

            if task.status == SubagentStatus.CANCELLED:
                raise RuntimeError(f"Task was cancelled: {task_id}")

            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Wait timeout for task: {task_id}")

            await asyncio.sleep(check_interval)

    async def _worker(self, worker_name: str):
        """
        Worker coroutine that processes tasks from the queue.

        Args:
            worker_name: Worker identifier for logging
        """
        logger.info(f"Worker started: {worker_name}")

        while self._running:
            try:
                # Get task from queue with timeout
                try:
                    task = await asyncio.wait_for(self._task_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Acquire semaphore
                async with self._semaphore:
                    logger.info(f"{worker_name} executing task: {task.id}")

                    # Update task status
                    async with self._task_lock:
                        self._tasks[task.id].status = SubagentStatus.RUNNING
                        self._tasks[task.id].start_time = time.time()

                    # Execute task
                    try:
                        timeout = task.metadata.get("timeout", self.default_timeout)
                        result = await asyncio.wait_for(
                            task.func(*task.args, **task.kwargs), timeout=timeout
                        )

                        # Update task result
                        async with self._task_lock:
                            self._tasks[task.id].status = SubagentStatus.COMPLETED
                            self._tasks[task.id].result = result
                            self._tasks[task.id].end_time = time.time()

                        logger.info(f"{worker_name} completed task: {task.id}")

                    except asyncio.TimeoutError:
                        error_msg = f"Task timeout after {timeout}s"
                        async with self._task_lock:
                            self._tasks[task.id].status = SubagentStatus.FAILED
                            self._tasks[task.id].error = error_msg
                            self._tasks[task.id].end_time = time.time()

                        logger.error(f"{worker_name} task timeout: {task.id}")

                    except Exception as e:
                        error_msg = str(e)
                        async with self._task_lock:
                            self._tasks[task.id].status = SubagentStatus.FAILED
                            self._tasks[task.id].error = error_msg
                            self._tasks[task.id].end_time = time.time()

                        logger.error(
                            f"{worker_name} task error: {task.id} - {error_msg}"
                        )

                    # Mark queue item as done
                    self._task_queue.task_done()

            except Exception as e:
                logger.error(f"{worker_name} error: {e}")
                await asyncio.sleep(0.1)

        logger.info(f"Worker stopped: {worker_name}")

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get manager statistics.

        Returns:
            Statistics dict
        """
        async with self._task_lock:
            tasks = list(self._tasks.values())

        total = len(tasks)
        pending = sum(1 for t in tasks if t.status == SubagentStatus.PENDING)
        running = sum(1 for t in tasks if t.status == SubagentStatus.RUNNING)
        completed = sum(1 for t in tasks if t.status == SubagentStatus.COMPLETED)
        failed = sum(1 for t in tasks if t.status == SubagentStatus.FAILED)
        cancelled = sum(1 for t in tasks if t.status == SubagentStatus.CANCELLED)

        # Calculate average execution time
        completed_tasks = [
            t
            for t in tasks
            if t.status == SubagentStatus.COMPLETED and t.start_time and t.end_time
        ]
        avg_time = 0.0
        if completed_tasks:
            total_time = sum(t.end_time - t.start_time for t in completed_tasks)
            avg_time = total_time / len(completed_tasks)

        return {
            "total_tasks": total,
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "queue_size": self._task_queue.qsize(),
            "available_workers": self._semaphore._value,
            "average_execution_time": avg_time,
            "is_running": self._running,
        }

    # ===== Resource Management =====

    def check_memory_usage(self) -> float:
        """
        Check current memory usage in MB.

        Returns:
            Memory usage in MB
        """
        memory_info = self._process.memory_info()
        return memory_info.rss / (1024 * 1024)

    def check_cpu_usage(self) -> float:
        """
        Check current CPU usage percentage.

        Returns:
            CPU usage percentage
        """
        return self._process.cpu_percent(interval=0.1)

    def can_submit_task(self) -> tuple[bool, str]:
        """
        Check if a new task can be submitted based on resources.

        Returns:
            (can_submit, reason) tuple
        """
        # Check memory
        if self.max_memory_mb:
            memory_mb = self.check_memory_usage()
            if memory_mb > self.max_memory_mb:
                return (
                    False,
                    f"Memory limit exceeded: {memory_mb:.2f}MB > {self.max_memory_mb}MB",
                )

        # Check CPU
        cpu_percent = self.check_cpu_usage()
        if cpu_percent > self.max_cpu_percent:
            return (
                False,
                f"CPU limit exceeded: {cpu_percent:.2f}% > {self.max_cpu_percent}%",
            )

        return True, "Resources available"

    async def _cleanup_loop(self):
        """Periodic cleanup of completed tasks."""
        logger.info("Started resource cleanup loop")

        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_completed_tasks()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")

        logger.info("Stopped resource cleanup loop")

    async def _cleanup_completed_tasks(self):
        """Clean up old completed tasks to free memory."""
        async with self._task_lock:
            # Find completed tasks
            completed_tasks = [
                (task_id, task)
                for task_id, task in self._tasks.items()
                if task.status
                in (
                    SubagentStatus.COMPLETED,
                    SubagentStatus.FAILED,
                    SubagentStatus.CANCELLED,
                )
            ]

            # If we have too many, remove the oldest ones
            if len(completed_tasks) > self._completed_task_retention:
                # Sort by end time (oldest first)
                completed_tasks.sort(key=lambda x: x[1].end_time or 0)

                # Remove excess tasks
                to_remove = completed_tasks[: -self._completed_task_retention]
                for task_id, task in to_remove:
                    del self._tasks[task_id]
                    logger.debug(f"Cleaned up task: {task_id}")

    async def cleanup_all_tasks(self):
        """Clean up all completed tasks."""
        async with self._task_lock:
            to_remove = [
                task_id
                for task_id, task in self._tasks.items()
                if task.status
                in (
                    SubagentStatus.COMPLETED,
                    SubagentStatus.FAILED,
                    SubagentStatus.CANCELLED,
                )
            ]

            for task_id in to_remove:
                del self._tasks[task_id]
                logger.debug(f"Cleaned up task: {task_id}")

        logger.info(f"Cleaned up {len(to_remove)} completed tasks")

    # ===== Lifecycle Management =====

    async def get_resource_stats(self) -> Dict[str, Any]:
        """
        Get detailed resource statistics.

        Returns:
            Resource statistics dict
        """
        return {
            "memory_mb": self.check_memory_usage(),
            "memory_limit_mb": self.max_memory_mb,
            "cpu_percent": self.check_cpu_usage(),
            "cpu_limit_percent": self.max_cpu_percent,
            "process_id": os.getpid(),
            "thread_count": self._process.num_threads(),
            "open_files": len(self._process.open_files()),
        }
