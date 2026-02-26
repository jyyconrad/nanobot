"""Tests for Phase 2 heartbeat refactoring."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from nanobot.heartbeat.service import HeartbeatService, _HEARTBEAT_TOOL
from nanobot.providers.base import LLMResponse, ToolCallRequest


class MockLLMProvider:
    """Mock LLM provider for testing."""

    def __init__(self):
        self.responses = []
        self.call_count = 0

    async def chat(self, messages, tools=None, model=None, **kwargs):
        """Mock chat method."""
        self.call_count += 1
        if self.responses:
            return self.responses.pop(0)
        return LLMResponse(content="OK", tool_calls=[])


class TestHeartbeatToolDefinition:
    """Test heartbeat tool definition."""

    def test_heartbeat_tool_structure(self):
        """Test that heartbeat tool has correct structure."""
        assert len(_HEARTBEAT_TOOL) == 1
        tool = _HEARTBEAT_TOOL[0]

        assert tool["type"] == "function"
        assert tool["function"]["name"] == "heartbeat"
        assert "action" in tool["function"]["parameters"]["properties"]
        assert "tasks" in tool["function"]["parameters"]["properties"]
        assert tool["function"]["parameters"]["required"] == ["action"]


class TestHeartbeatDecide:
    """Test heartbeat decision mechanism."""

    @pytest.mark.asyncio
    async def test_decide_returns_skip_when_no_tool_calls(self, tmp_path):
        """Test that decide returns 'skip' when no tool calls."""
        provider = MockLLMProvider()
        provider.responses.append(LLMResponse(content="OK", tool_calls=[]))

        service = HeartbeatService(
            workspace=tmp_path,
            provider=provider,
            model="test-model",
        )

        action, tasks = await service._decide("test content")

        assert action == "skip"
        assert tasks == ""

    @pytest.mark.asyncio
    async def test_decide_returns_run_when_tool_called(self, tmp_path):
        """Test that decide returns 'run' when tool is called."""
        provider = MockLLMProvider()
        provider.responses.append(
            LLMResponse(
                content="OK",
                tool_calls=[
                    ToolCallRequest(
                        id="1",
                        name="heartbeat",
                        arguments={"action": "run", "tasks": "Task 1"},
                    )
                ],
            )
        )

        service = HeartbeatService(
            workspace=tmp_path,
            provider=provider,
            model="test-model",
        )

        action, tasks = await service._decide("test content")

        assert action == "run"
        assert tasks == "Task 1"

    @pytest.mark.asyncio
    async def test_decide_defaults_to_skip_if_missing_action(self, tmp_path):
        """Test that decide defaults to 'skip' if action is missing."""
        provider = MockLLMProvider()
        provider.responses.append(
            LLMResponse(
                content="OK",
                tool_calls=[
                    ToolCallRequest(
                        id="1",
                        name="heartbeat",
                        arguments={},
                    )
                ],
            )
        )

        service = HeartbeatService(
            workspace=tmp_path,
            provider=provider,
            model="test-model",
        )

        action, tasks = await service._decide("test content")

        assert action == "skip"


class TestHeartbeatSilent:
    """Test that heartbeat is silent when no tasks."""

    @pytest.mark.asyncio
    async def test_tick_skips_when_heartbeat_file_empty(self, tmp_path):
        """Test that tick skips when HEARTBEAT.md is empty."""
        provider = MockLLMProvider()
        llm_call_count = 0

        async def mock_chat(*args, **kwargs):
            nonlocal llm_call_count
            llm_call_count += 1
            return LLMResponse(content="OK", tool_calls=[])

        provider.chat = mock_chat

        # Don't create HEARTBEAT.md file
        service = HeartbeatService(
            workspace=tmp_path,
            provider=provider,
            model="test-model",
        )

        await service._tick()

        # Should not call LLM when file is missing
        assert llm_call_count == 0

    @pytest.mark.asyncio
    async def test_tick_calls_llm_when_heartbeat_file_exists(self, tmp_path):
        """Test that tick calls LLM when HEARTBEAT.md exists."""
        # Create HEARTBEAT.md with content
        heartbeat_file = tmp_path / "HEARTBEAT.md"
        heartbeat_file.write_text("# Tasks\n- [ ] Task 1")

        provider = MockLLMProvider()
        llm_call_count = 0

        async def mock_chat(*args, **kwargs):
            nonlocal llm_call_count
            llm_call_count += 1
            return LLMResponse(
                content="OK",
                tool_calls=[
                    ToolCallRequest(
                        id="1",
                        name="heartbeat",
                        arguments={"action": "skip"},
                    )
                ],
            )

        provider.chat = mock_chat

        service = HeartbeatService(
            workspace=tmp_path,
            provider=provider,
            model="test-model",
        )

        await service._tick()

        # Should call LLM when file exists with content
        assert llm_call_count == 1


class TestHeartbeatExecution:
    """Test heartbeat execution flow."""

    @pytest.mark.asyncio
    async def test_tick_executes_task_when_action_is_run(self, tmp_path):
        """Test that tick executes task when action is 'run'."""
        # Create HEARTBEAT.md with content
        heartbeat_file = tmp_path / "HEARTBEAT.md"
        heartbeat_file.write_text("# Tasks\n- [ ] Task 1")

        provider = MockLLMProvider()
        execute_called = False
        execute_tasks = None

        async def mock_execute(tasks):
            nonlocal execute_called, execute_tasks
            execute_called = True
            execute_tasks = tasks
            return "Task completed"

        async def mock_chat(*args, **kwargs):
            return LLMResponse(
                content="OK",
                tool_calls=[
                    ToolCallRequest(
                        id="1",
                        name="heartbeat",
                        arguments={"action": "run", "tasks": "Task 1"},
                    )
                ],
            )

        provider.chat = mock_chat

        service = HeartbeatService(
            workspace=tmp_path,
            provider=provider,
            model="test-model",
            on_execute=mock_execute,
        )

        await service._tick()

        assert execute_called
        assert execute_tasks == "Task 1"

    @pytest.mark.asyncio
    async def test_tick_notifies_when_task_completes(self, tmp_path):
        """Test that tick notifies when task completes."""
        heartbeat_file = tmp_path / "HEARTBEAT.md"
        heartbeat_file.write_text("# Tasks")

        provider = MockLLMProvider()
        notify_called = False
        notify_response = None

        async def mock_execute(tasks):
            return "Task completed"

        async def mock_notify(response):
            nonlocal notify_called, notify_response
            notify_called = True
            notify_response = response

        async def mock_chat(*args, **kwargs):
            return LLMResponse(
                content="OK",
                tool_calls=[
                    ToolCallRequest(
                        id="1",
                        name="heartbeat",
                        arguments={"action": "run", "tasks": "Task 1"},
                    )
                ],
            )

        provider.chat = mock_chat

        service = HeartbeatService(
            workspace=tmp_path,
            provider=provider,
            model="test-model",
            on_execute=mock_execute,
            on_notify=mock_notify,
        )

        await service._tick()

        assert notify_called
        assert notify_response == "Task completed"


class TestHeartbeatStartStop:
    """Test heartbeat start/stop functionality."""

    @pytest.mark.asyncio
    async def test_start_creates_task(self, tmp_path):
        """Test that start creates a background task."""
        provider = MockLLMProvider()

        service = HeartbeatService(
            workspace=tmp_path,
            provider=provider,
            model="test-model",
            interval_s=1,  # 1 second for testing
        )

        await service.start()

        assert service._running
        assert service._task is not None

        # Cleanup
        service.stop()

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self, tmp_path):
        """Test that stop cancels the background task."""
        provider = MockLLMProvider()

        service = HeartbeatService(
            workspace=tmp_path,
            provider=provider,
            model="test-model",
            interval_s=60,
        )

        await service.start()
        assert service._running

        service.stop()

        assert not service._running
        assert service._task is None

    @pytest.mark.asyncio
    async def test_start_idempotent(self, tmp_path):
        """Test that start is idempotent (doesn't start multiple times)."""
        provider = MockLLMProvider()

        service = HeartbeatService(
            workspace=tmp_path,
            provider=provider,
            model="test-model",
        )

        await service.start()
        first_task = service._task

        # Try to start again
        await service.start()

        # Should be the same task
        assert service._task == first_task

        # Cleanup
        service.stop()


class TestHeartbeatIntegration:
    """Integration tests for heartbeat service."""

    @pytest.mark.asyncio
    async def test_full_heartbeat_cycle_skip(self, tmp_path):
        """Test full heartbeat cycle with skip action."""
        # Create HEARTBEAT.md
        heartbeat_file = tmp_path / "HEARTBEAT.md"
        heartbeat_file.write_text("# No tasks")

        provider = MockLLMProvider()

        async def mock_chat(*args, **kwargs):
            return LLMResponse(
                content="OK",
                tool_calls=[
                    ToolCallRequest(
                        id="1",
                        name="heartbeat",
                        arguments={"action": "skip"},
                    )
                ],
            )

        provider.chat = mock_chat

        service = HeartbeatService(
            workspace=tmp_path,
            provider=provider,
            model="test-model",
        )

        await service._tick()

        # Should complete without errors

    @pytest.mark.asyncio
    async def test_full_heartbeat_cycle_run(self, tmp_path):
        """Test full heartbeat cycle with run action."""
        heartbeat_file = tmp_path / "HEARTBEAT.md"
        heartbeat_file.write_text("# Task 1")

        execute_results = []

        async def mock_execute(tasks):
            execute_results.append(tasks)
            return f"Completed: {tasks}"

        async def mock_chat(*args, **kwargs):
            return LLMResponse(
                content="OK",
                tool_calls=[
                    ToolCallRequest(
                        id="1",
                        name="heartbeat",
                        arguments={"action": "run", "tasks": "Task 1"},
                    )
                ],
            )

        provider = MockLLMProvider()
        provider.chat = mock_chat

        service = HeartbeatService(
            workspace=tmp_path,
            provider=provider,
            model="test-model",
            on_execute=mock_execute,
        )

        await service._tick()

        assert len(execute_results) == 1
        assert execute_results[0] == "Task 1"
