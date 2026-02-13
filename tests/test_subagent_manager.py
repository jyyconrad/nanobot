"""Tests for SubagentManager."""

import asyncio
import pytest
from nanobot.agents.subagent_manager import (
    SubagentManager,
    SubagentTask,
    SubagentStatus
)


class TestSubagentManager:
    """Test suite for SubagentManager."""

    @pytest.mark.asyncio
    async def test_manager_initialization(self):
        """Test manager initialization."""
        manager = SubagentManager(max_concurrent=5, timeout=300.0)
        assert manager.max_concurrent == 5
        assert manager.default_timeout == 300.0
        assert not manager._running

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test start and stop."""
        manager = SubagentManager(max_concurrent=3)
        await manager.start()
        assert manager._running
        await manager.stop()
        assert not manager._running

    @pytest.mark.asyncio
    async def test_submit_task(self):
        """Test task submission."""
        manager = SubagentManager(max_concurrent=3)
        await manager.start()

        async def sample_task(x, y):
            return x + y

        task_id = await manager.submit_task(
            "task-1",
            "Test Task",
            sample_task,
            2, 3
        )

        assert task_id == "task-1"
        task = await manager.get_task(task_id)
        assert task is not None
        assert task.id == "task-1"
        assert task.name == "Test Task"

        await manager.stop()

    @pytest.mark.asyncio
    async def test_task_execution(self):
        """Test task execution."""
        manager = SubagentManager(max_concurrent=3)
        await manager.start()

        async def sample_task(x, y):
            await asyncio.sleep(0.1)
            return x + y

        task_id = await manager.submit_task(
            "task-2",
            "Add Task",
            sample_task,
            10, 20
        )

        # Wait for task completion
        result = await manager.wait_for_task(task_id, timeout=5.0)
        assert result == 30

        task = await manager.get_task(task_id)
        assert task.status == SubagentStatus.COMPLETED

        await manager.stop()

    @pytest.mark.asyncio
    async def test_concurrent_limit(self):
        """Test concurrent execution limit."""
        manager = SubagentManager(max_concurrent=2)
        await manager.start()

        running_count = 0
        max_running = 0
        lock = asyncio.Lock()

        async def counting_task():
            nonlocal running_count, max_running
            async with lock:
                running_count += 1
                max_running = max(max_running, running_count)

            await asyncio.sleep(0.2)

            async with lock:
                running_count -= 1

            return "done"

        # Submit 5 tasks
        task_ids = []
        for i in range(5):
            task_id = await manager.submit_task(
                f"task-{i}",
                f"Counting Task {i}",
                counting_task
            )
            task_ids.append(task_id)

        # Wait for all tasks
        for task_id in task_ids:
            await manager.wait_for_task(task_id, timeout=10.0)

        # Verify max concurrent was 2
        assert max_running <= 2

        await manager.stop()

    @pytest.mark.asyncio
    async def test_task_failure(self):
        """Test task failure handling."""
        manager = SubagentManager(max_concurrent=3)
        await manager.start()

        async def failing_task():
            await asyncio.sleep(0.1)
            raise ValueError("Task failed")

        task_id = await manager.submit_task(
            "task-fail",
            "Failing Task",
            failing_task
        )

        # Wait for task to complete (will fail)
        with pytest.raises(RuntimeError):
            await manager.wait_for_task(task_id, timeout=5.0)

        task = await manager.get_task(task_id)
        assert task.status == SubagentStatus.FAILED
        assert "Task failed" in task.error

        await manager.stop()

    @pytest.mark.asyncio
    async def test_task_timeout(self):
        """Test task timeout handling."""
        manager = SubagentManager(max_concurrent=3, timeout=0.5)
        await manager.start()

        async def slow_task():
            await asyncio.sleep(2.0)
            return "done"

        task_id = await manager.submit_task(
            "task-slow",
            "Slow Task",
            slow_task
        )

        # Wait for task to fail with timeout
        with pytest.raises(RuntimeError):
            await manager.wait_for_task(task_id, timeout=5.0)

        task = await manager.get_task(task_id)
        assert task.status == SubagentStatus.FAILED
        assert "timeout" in task.error.lower()

        await manager.stop()

    @pytest.mark.asyncio
    async def test_task_cancellation(self):
        """Test task cancellation."""
        manager = SubagentManager(max_concurrent=3)
        await manager.start()

        async def long_task():
            await asyncio.sleep(10.0)
            return "done"

        task_id = await manager.submit_task(
            "task-cancel",
            "Long Task",
            long_task
        )

        # Cancel the task
        cancelled = await manager.cancel_task(task_id)
        assert cancelled

        task = await manager.get_task(task_id)
        assert task.status == SubagentStatus.CANCELLED

        await manager.stop()

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test statistics gathering."""
        manager = SubagentManager(max_concurrent=3)
        await manager.start()

        async def quick_task():
            return "done"

        # Submit some tasks
        for i in range(3):
            await manager.submit_task(
                f"task-{i}",
                f"Quick Task {i}",
                quick_task
            )

        stats = await manager.get_stats()
        assert stats["total_tasks"] >= 3
        assert stats["is_running"]
        assert "running" in stats
        assert "completed" in stats

        await manager.stop()

    @pytest.mark.asyncio
    async def test_multiple_tasks(self):
        """Test multiple concurrent tasks."""
        manager = SubagentManager(max_concurrent=5)
        await manager.start()

        results = []

        async def multiply_task(a, b):
            await asyncio.sleep(0.1)
            return a * b

        # Submit multiple tasks
        task_ids = []
        for i in range(10):
            task_id = await manager.submit_task(
                f"mult-task-{i}",
                f"Multiply Task {i}",
                multiply_task,
                i, i + 1
            )
            task_ids.append(task_id)

        # Collect results
        for task_id in task_ids:
            result = await manager.wait_for_task(task_id, timeout=10.0)
            results.append(result)

        # Verify results
        assert len(results) == 10
        assert results == [i * (i + 1) for i in range(10)]

        await manager.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
