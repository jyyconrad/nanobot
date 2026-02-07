"""Tests for Agno-based Subagent infrastructure."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from nanobot.agent.subagent.agno_subagent import (
    AgnoSubagent,
    AgnoSubagentConfig,
    AgnoSubagentManager,
)
from nanobot.agent.task import TaskStatus
from nanobot.bus.queue import MessageBus
from nanobot.providers.base import LLMProvider


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_provider():
    """Create a mock LLM provider."""
    provider = MagicMock(spec=LLMProvider)
    provider.get_default_model.return_value = "default-model"
    return provider


@pytest.fixture
def mock_bus():
    """Create a mock message bus."""
    bus = MagicMock(spec=MessageBus)

    async def mock_publish(*args, **kwargs):
        pass

    bus.publish_inbound = mock_publish
    return bus


@pytest.fixture
def config():
    """Create a default AgnoSubagentConfig."""
    return AgnoSubagentConfig()


class TestAgnoSubagentConfig:
    """Tests for AgnoSubagentConfig model."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = AgnoSubagentConfig()
        assert config.max_iterations == 15
        assert config.timeout == 300
        assert config.model is None
        assert config.brave_api_key is None
        assert config.restrict_to_workspace is True

    def test_config_customization(self):
        """Test configuration customization."""
        config = AgnoSubagentConfig(
            max_iterations=20,
            timeout=600,
            model="gpt-4",
            brave_api_key="test-key",
            restrict_to_workspace=False,
        )
        assert config.max_iterations == 20
        assert config.timeout == 600
        assert config.model == "gpt-4"
        assert config.brave_api_key == "test-key"
        assert config.restrict_to_workspace is False


class TestAgnoSubagent:
    """Tests for AgnoSubagent data model."""

    def test_agno_subagent_creation(self):
        """Test AgnoSubagent initialization."""
        subagent = AgnoSubagent(
            subagent_id="test-1234", task_id="task-5678", task="Test task", label="Test label"
        )

        assert subagent.subagent_id == "test-1234"
        assert subagent.task_id == "task-5678"
        assert subagent.task == "Test task"
        assert subagent.label == "Test label"
        assert subagent.status == TaskStatus.RUNNING
        assert subagent.progress == 0.0
        assert subagent.iteration == 0

    def test_agno_subagent_progress(self):
        """Test progress tracking."""
        subagent = AgnoSubagent(
            subagent_id="test-1234", task_id="task-5678", task="Test task", label="Test label"
        )

        subagent.iteration = 5
        subagent.progress = 33.3

        assert subagent.iteration == 5
        assert subagent.progress == 33.3

    def test_agno_subagent_status_transition(self):
        """Test status transition methods."""
        subagent = AgnoSubagent(
            subagent_id="test-1234", task_id="task-5678", task="Test task", label="Test label"
        )

        # Initially running
        assert subagent.status == TaskStatus.RUNNING

        # Set to completed
        subagent.status = TaskStatus.COMPLETED
        assert subagent.status == TaskStatus.COMPLETED

        # Set to failed
        subagent.status = TaskStatus.FAILED
        assert subagent.status == TaskStatus.FAILED


class TestAgnoSubagentManager:
    """Tests for AgnoSubagentManager."""

    @pytest.mark.asyncio
    async def test_manager_initialization(self, mock_provider, temp_workspace, mock_bus, config):
        """Test AgnoSubagentManager initialization."""
        manager = AgnoSubagentManager(
            provider=mock_provider, workspace=temp_workspace, bus=mock_bus, config=config
        )

        await manager.initialize()

        assert manager.provider == mock_provider
        assert manager.workspace == temp_workspace
        assert manager.bus == mock_bus
        assert manager.config == config
        assert manager._risk_evaluator is not None
        assert manager._interrupt_handler is not None
        assert manager._hooks is not None
        assert len(manager._subagent_map) == 0
        assert len(manager._task_map) == 0

    @pytest.mark.asyncio
    async def test_spawn_subagent(self, mock_provider, temp_workspace, mock_bus, config):
        """Test spawning a subagent."""
        manager = AgnoSubagentManager(
            provider=mock_provider, workspace=temp_workspace, bus=mock_bus, config=config
        )

        await manager.initialize()
        subagent_id = await manager.spawn("Test task", "Test label")

        assert subagent_id is not None
        assert len(subagent_id) == 8
        assert subagent_id in manager._subagent_map
        assert len(manager._running_tasks) == 1

        subagent = manager.get_subagent_by_id(subagent_id)
        assert subagent is not None
        assert subagent.task == "Test task"
        assert subagent.label == "Test label"
        assert subagent.status == TaskStatus.RUNNING

    @pytest.mark.asyncio
    async def test_spawn_with_long_task(self, mock_provider, temp_workspace, mock_bus, config):
        """Test spawning with long task description."""
        manager = AgnoSubagentManager(
            provider=mock_provider, workspace=temp_workspace, bus=mock_bus, config=config
        )

        await manager.initialize()
        long_task = "This is a very long task description that should be truncated" * 2
        subagent_id = await manager.spawn(long_task)

        subagent = manager.get_subagent_by_id(subagent_id)
        assert len(subagent.label) <= 33  # 30 chars + "..."
        assert "..." in subagent.label

    @pytest.mark.asyncio
    async def test_cancel_subagent(self, mock_provider, temp_workspace, mock_bus, config):
        """Test cancelling a subagent."""
        manager = AgnoSubagentManager(
            provider=mock_provider, workspace=temp_workspace, bus=mock_bus, config=config
        )

        await manager.initialize()
        subagent_id = await manager.spawn("Test task")

        # Cancel the subagent
        cancelled = await manager.cancel_subagent(subagent_id)

        assert cancelled is True

        subagent = manager.get_subagent_by_id(subagent_id)
        assert subagent.status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_get_subagent_by_task_id(self, mock_provider, temp_workspace, mock_bus, config):
        """Test getting subagent by task ID."""
        manager = AgnoSubagentManager(
            provider=mock_provider, workspace=temp_workspace, bus=mock_bus, config=config
        )

        await manager.initialize()
        subagent_id = await manager.spawn("Test task")
        subagent = manager.get_subagent_by_id(subagent_id)

        assert subagent is not None

        found_subagent = manager.get_subagent_by_task_id(subagent.task_id)
        assert found_subagent is not None
        assert found_subagent.subagent_id == subagent_id

    def test_running_count(self, mock_provider, temp_workspace, mock_bus, config):
        """Test getting running count."""
        manager = AgnoSubagentManager(
            provider=mock_provider, workspace=temp_workspace, bus=mock_bus, config=config
        )

        assert manager.get_running_count() == 0

    def test_get_all_subagents(self, mock_provider, temp_workspace, mock_bus, config):
        """Test getting all subagents."""
        manager = AgnoSubagentManager(
            provider=mock_provider, workspace=temp_workspace, bus=mock_bus, config=config
        )

        assert len(manager.get_all_subagents()) == 0

    @pytest.mark.asyncio
    async def test_get_task_manager(self, mock_provider, temp_workspace, mock_bus, config):
        """Test getting task manager."""
        manager = AgnoSubagentManager(
            provider=mock_provider, workspace=temp_workspace, bus=mock_bus, config=config
        )

        task_manager = manager.get_task_manager()
        assert task_manager is not None
        assert hasattr(task_manager, "create_task")
        assert hasattr(task_manager, "get_task")

    @pytest.mark.asyncio
    async def test_get_progress_tracker(self, mock_provider, temp_workspace, mock_bus, config):
        """Test getting progress tracker."""
        manager = AgnoSubagentManager(
            provider=mock_provider, workspace=temp_workspace, bus=mock_bus, config=config
        )

        progress_tracker = manager.get_progress_tracker()
        assert progress_tracker is not None
        assert hasattr(progress_tracker, "track_progress")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
