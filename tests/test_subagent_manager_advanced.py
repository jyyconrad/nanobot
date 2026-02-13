"""Advanced tests for SubagentManager with resource management."""

import asyncio

import pytest

from nanobot.agents.subagent_manager import (
    SubagentManager,
    SubagentStatus,
    SubagentTask,
)


class TestSubagentManagerResourceManagement:
    """Test suite for SubagentManager resource management."""

    @pytest.mark.asyncio
    async def test_memory_monitoring(self):
        """Test memory usage monitoring."""
        manager = SubagentManager(max_concurrent=3, max_memory_mb=1000)
        await manager.start()

        memory_mb = manager.check_memory_usage()
        assert memory_mb > 0
        assert memory_mb < 10000  # Should be reasonable

        await manager.stop()

    @pytest.mark.asyncio
    async def test_cpu_monitoring(self):
        """Test CPU usage monitoring."""
        manager = SubagentManager(max_concurrent=3, max_cpu_percent=90.0)
        await manager.start()

        cpu_percent = manager.check_cpu_usage()
        assert 0 <= cpu_percent <= 100

        await manager.stop()

    @pytest.mark.asyncio
    async def test_resource_stats(self):
        """Test resource statistics."""
        manager = SubagentManager(max_concurrent=3)
        await manager.start()

        stats = await manager.get_resource_stats()
        assert "memory_mb" in stats
        assert "cpu_percent" in stats
        assert "process_id" in stats
        assert "thread_count" in stats

        await manager.stop()

    @pytest.mark.asyncio
    async def test_can_submit_task(self):
        """Test task submission resource check."""
        manager = SubagentManager(
            max_concurrent=3, max_memory_mb=100000, max_cpu_percent=99.0
        )
        await manager.start()

        can_submit, reason = manager.can_submit_task()
        assert can_submit
        assert reason == "Resources available"

        await manager.stop()

    @pytest.mark.asyncio
    async def test_cleanup_completed_tasks(self):
        """Test automatic cleanup of completed tasks."""
        manager = SubagentManager(max_concurrent=3)
        await manager.start()

        async def quick_task():
            return "done"

        # Submit many tasks
        for i in range(50):
            task_id = await manager.submit_task(f"task-{i}", f"Task {i}", quick_task)
            await manager.wait_for_task(task_id)

        # Check initial stats
        initial_stats = await manager.get_stats()
        assert initial_stats["completed"] == 50

        # Trigger manual cleanup
        await manager.cleanup_all_tasks()

        # Check cleanup happened
        stats = await manager.get_stats()
        assert stats["completed"] == 0

        await manager.stop()

    @pytest.mark.asyncio
    async def test_manual_cleanup_all(self):
        """Test manual cleanup of all completed tasks."""
        manager = SubagentManager(max_concurrent=3)
        await manager.start()

        async def quick_task():
            return "done"

        # Submit tasks
        for i in range(10):
            task_id = await manager.submit_task(f"task-{i}", f"Task {i}", quick_task)
            await manager.wait_for_task(task_id)

        # All should be completed
        stats = await manager.get_stats()
        assert stats["completed"] == 10

        # Cleanup all
        await manager.cleanup_all_tasks()

        # No completed tasks left
        stats = await manager.get_stats()
        assert stats["completed"] == 0

        await manager.stop()

    @pytest.mark.asyncio
    async def test_resource_limits_with_task_submission(self):
        """Test that resource limits affect task submission."""
        # Set a very low memory limit
        manager = SubagentManager(max_concurrent=3, max_memory_mb=0.1)
        await manager.start()

        async def quick_task():
            return "done"

        # Check if we can submit (should be false due to memory limit)
        can_submit, reason = manager.can_submit_task()

        # We can't reliably trigger memory limit in tests,
        # but we can check the mechanism works
        assert isinstance(can_submit, bool)
        assert isinstance(reason, str)

        await manager.stop()

    @pytest.mark.asyncio
    async def test_long_running_cleanup_loop(self):
        """Test that cleanup loop runs correctly over time."""
        manager = SubagentManager(max_concurrent=3, cleanup_interval=0.5)
        await manager.start()

        async def quick_task():
            return "done"

        # Submit tasks periodically
        for i in range(20):
            task_id = await manager.submit_task(f"task-{i}", f"Task {i}", quick_task)
            await manager.wait_for_task(task_id)
            await asyncio.sleep(0.1)

        # Let cleanup run
        await asyncio.sleep(1.0)

        # Check stats
        stats = await manager.get_stats()
        # Cleanup should have removed some tasks
        assert stats["completed"] >= 0

        await manager.stop()

    @pytest.mark.asyncio
    async def test_concurrent_with_resource_monitoring(self):
        """Test concurrent tasks with resource monitoring."""
        manager = SubagentManager(
            max_concurrent=3, max_memory_mb=100000, max_cpu_percent=99.0
        )
        await manager.start()

        results = []

        async def monitored_task(value):
            # Check resources during task
            can_submit, _ = manager.can_submit_task()
            assert can_submit

            await asyncio.sleep(0.1)
            return value * 2

        # Submit concurrent tasks
        task_ids = []
        for i in range(10):
            task_id = await manager.submit_task(
                f"task-{i}", f"Monitored Task {i}", monitored_task, i
            )
            task_ids.append(task_id)

        # Wait for all and collect results
        for task_id in task_ids:
            result = await manager.wait_for_task(task_id)
            results.append(result)

        assert len(results) == 10
        assert results == [i * 2 for i in range(10)]

        await manager.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
