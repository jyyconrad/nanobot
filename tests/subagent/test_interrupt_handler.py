"""Tests for InterruptHandler component."""

import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from nanobot.agent.subagent.agno_subagent import AgnoSubagentManager
from nanobot.agent.subagent.interrupt_handler import (
    InterruptHandler,
    InterruptRequest,
    InterruptType,
)
from nanobot.bus.events import InboundMessage


@pytest.fixture
def mock_manager():
    """Create a mock AgnoSubagentManager."""
    manager = MagicMock(spec=AgnoSubagentManager)
    manager.bus = MagicMock()

    async def mock_publish(*args, **kwargs):
        pass

    manager.bus.publish_inbound = mock_publish

    async def mock_cancel(*args, **kwargs):
        return True

    async def mock_spawn(*args, **kwargs):
        return "new-subagent-id"

    manager.cancel_subagent = mock_cancel
    manager.spawn = mock_spawn
    manager._subagent_map = {}
    return manager


class TestInterruptType:
    """Tests for InterruptType model."""

    def test_interrupt_type_creation(self):
        """Test InterruptType initialization."""
        interrupt_type = InterruptType(
            type="cancel", priority=5, description="Cancel task immediately"
        )

        assert interrupt_type.type == "cancel"
        assert interrupt_type.priority == 5
        assert interrupt_type.description == "Cancel task immediately"


class TestInterruptRequest:
    """Tests for InterruptRequest model."""

    def test_interrupt_request_creation(self):
        """Test InterruptRequest initialization."""
        request = InterruptRequest(
            request_id="intr-1234",
            subagent_id="test-1234",
            type="cancel",
            message="Cancel the task",
        )

        assert request.request_id == "intr-1234"
        assert request.subagent_id == "test-1234"
        assert request.type == "cancel"
        assert request.message == "Cancel the task"
        assert isinstance(request.timestamp, datetime)
        assert request.processed is False

    def test_interrupt_request_processed(self):
        """Test marking request as processed."""
        request = InterruptRequest(
            request_id="intr-1234",
            subagent_id="test-1234",
            type="cancel",
            message="Cancel the task",
        )

        request.processed = True
        assert request.processed is True


class TestInterruptHandler:
    """Tests for InterruptHandler component."""

    def test_initialization(self, mock_manager):
        """Test InterruptHandler initialization."""
        handler = InterruptHandler(mock_manager)

        assert handler.manager == mock_manager
        assert handler.bus == mock_manager.bus
        assert len(handler._pending_interrupts) == 0
        assert len(handler._paused_subagents) == 0
        assert len(handler._interrupt_types) > 0

    def test_get_interrupt_type(self, mock_manager):
        """Test getting interrupt type details."""
        handler = InterruptHandler(mock_manager)

        cancel_type = handler.get_interrupt_type("cancel")
        assert cancel_type is not None
        assert cancel_type.type == "cancel"
        assert cancel_type.priority == 5

        pause_type = handler.get_interrupt_type("pause")
        assert pause_type is not None
        assert pause_type.type == "pause"
        assert pause_type.priority == 3

        unknown_type = handler.get_interrupt_type("unknown")
        assert unknown_type is None

    @pytest.mark.asyncio
    async def test_add_interrupt(self, mock_manager):
        """Test adding interrupt request."""
        handler = InterruptHandler(mock_manager)

        request = await handler.add_interrupt("test-1234", "cancel", "Cancel task")

        assert request is not None
        assert request.request_id.startswith("intr_")
        assert request.subagent_id == "test-1234"
        assert request.type == "cancel"
        assert request.message == "Cancel task"
        assert len(handler._pending_interrupts) == 1
        assert "test-1234" in handler._pending_interrupts

    @pytest.mark.asyncio
    async def test_add_unknown_interrupt(self, mock_manager):
        """Test adding an unknown interrupt type."""
        handler = InterruptHandler(mock_manager)

        request = await handler.add_interrupt("test-1234", "unknown", "Test")

        assert request is None
        assert len(handler._pending_interrupts) == 0

    @pytest.mark.asyncio
    async def test_cancel_interrupt(self, mock_manager):
        """Test cancelling an interrupt request."""
        handler = InterruptHandler(mock_manager)

        request = await handler.add_interrupt("test-1234", "cancel", "Cancel task")
        assert request is not None

        await handler.cancel_interrupt(request.request_id)
        assert len(handler._pending_interrupts) == 0

    @pytest.mark.asyncio
    async def test_check_for_interrupt(self, mock_manager):
        """Test checking for interrupts."""
        handler = InterruptHandler(mock_manager)

        # No interrupt
        has_interrupt = await handler.check_for_interrupt("test-1234")
        assert has_interrupt is False

        # With interrupt
        await handler.add_interrupt("test-1234", "cancel", "Cancel task")
        assert "test-1234" in handler._pending_interrupts

        with patch.object(handler, "_handle_interrupt") as mock_handle:

            async def mock_handle_func(*args, **kwargs):
                pass

            mock_handle.side_effect = mock_handle_func
            has_interrupt = await handler.check_for_interrupt("test-1234")
            assert has_interrupt is True
            assert mock_handle.called

    def test_is_subagent_paused(self, mock_manager):
        """Test checking if subagent is paused."""
        handler = InterruptHandler(mock_manager)

        # Not paused
        assert handler.is_subagent_paused("test-1234") is False

        # Paused
        handler._paused_subagents.add("test-1234")
        assert handler.is_subagent_paused("test-1234") is True

    def test_get_paused_subagents(self, mock_manager):
        """Test getting paused subagents."""
        handler = InterruptHandler(mock_manager)

        handler._paused_subagents.add("test-1234")
        handler._paused_subagents.add("test-5678")

        paused = handler.get_paused_subagents()
        assert len(paused) == 2
        assert "test-1234" in paused
        assert "test-5678" in paused

    @pytest.mark.asyncio
    async def test_handle_message_interrupt_cancel(self, mock_manager):
        """Test handling cancel interrupt from message."""
        handler = InterruptHandler(mock_manager)

        message = InboundMessage(
            channel="system",
            sender_id="user",
            chat_id="direct",
            content="Cancel subagent [abcd1234]",
        )

        with patch.object(handler, "add_interrupt") as mock_add:

            async def mock_add_func(*args, **kwargs):
                return None

            mock_add.side_effect = mock_add_func
            result = await handler.handle_message_interrupt(message)
            assert result is True
            mock_add.assert_called_once_with(
                "abcd1234", "cancel", "Cancel subagent [abcd1234]"
            )

    @pytest.mark.asyncio
    async def test_handle_message_interrupt_pause(self, mock_manager):
        """Test handling pause interrupt from message."""
        handler = InterruptHandler(mock_manager)

        message = InboundMessage(
            channel="system",
            sender_id="user",
            chat_id="direct",
            content="Pause subagent [abcd1234]",
        )

        with patch.object(handler, "add_interrupt") as mock_add:

            async def mock_add_func(*args, **kwargs):
                return None

            mock_add.side_effect = mock_add_func
            result = await handler.handle_message_interrupt(message)
            assert result is True
            mock_add.assert_called_once_with(
                "abcd1234", "pause", "Pause subagent [abcd1234]"
            )

    @pytest.mark.asyncio
    async def test_handle_message_interrupt_correct(self, mock_manager):
        """Test handling correct interrupt from message."""
        handler = InterruptHandler(mock_manager)

        message = InboundMessage(
            channel="system",
            sender_id="user",
            chat_id="direct",
            content="Correct subagent [abcd1234] to do something else",
        )

        with patch.object(handler, "add_interrupt") as mock_add:

            async def mock_add_func(*args, **kwargs):
                return None

            mock_add.side_effect = mock_add_func
            result = await handler.handle_message_interrupt(message)
            assert result is True
            mock_add.assert_called_once_with(
                "abcd1234", "correct", "to do something else"
            )

    @pytest.mark.asyncio
    async def test_handle_unknown_message(self, mock_manager):
        """Test handling an unknown message as interrupt."""
        handler = InterruptHandler(mock_manager)

        message = InboundMessage(
            channel="system",
            sender_id="user",
            chat_id="direct",
            content="Unknown command",
        )

        result = await handler.handle_message_interrupt(message)
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_all_interrupts(self, mock_manager):
        """Test cancelling all pending interrupts."""
        handler = InterruptHandler(mock_manager)

        await handler.add_interrupt("test-1234", "cancel", "Cancel task 1")
        await handler.add_interrupt("test-5678", "pause", "Pause task 2")

        assert len(handler._pending_interrupts) == 2

        await handler.cancel_all_pending_interrupts()
        assert len(handler._pending_interrupts) == 0

    @pytest.mark.asyncio
    async def test_pause_all_subagents(self, mock_manager):
        """Test pausing all subagents."""
        handler = InterruptHandler(mock_manager)

        # Create mock subagents
        mock_subagent1 = MagicMock()
        mock_subagent1.status = "running"
        mock_subagent2 = MagicMock()
        mock_subagent2.status = "running"

        handler.manager._subagent_map = {
            "test-1234": mock_subagent1,
            "test-5678": mock_subagent2,
        }

        await handler.pause_all_subagents()
        assert len(handler._paused_subagents) == 2

    @pytest.mark.asyncio
    async def test_resume_all_subagents(self, mock_manager):
        """Test resuming all subagents."""
        handler = InterruptHandler(mock_manager)

        handler._paused_subagents.add("test-1234")
        handler._paused_subagents.add("test-5678")

        assert len(handler._paused_subagents) == 2

        await handler.resume_all_subagents()
        assert len(handler._paused_subagents) == 0

    @pytest.mark.asyncio
    async def test_wait_for_resume_immediate(self, mock_manager):
        """Test waiting for resume when already running."""
        handler = InterruptHandler(mock_manager)

        result = await handler.wait_for_resume("test-1234", timeout=1)
        assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_resume_timeout(self, mock_manager):
        """Test waiting for resume with timeout."""
        handler = InterruptHandler(mock_manager)

        handler._paused_subagents.add("test-1234")

        with patch("asyncio.sleep") as mock_sleep:
            mock_sleep.side_effect = lambda x: asyncio.sleep(0)
            result = await handler.wait_for_resume("test-1234", timeout=0.001)
            assert result is False

    @pytest.mark.asyncio
    async def test_handle_cancel_interrupt(self, mock_manager):
        """Test handling cancel interrupt."""
        handler = InterruptHandler(mock_manager)
        subagent_id = "test-1234"

        with patch.object(handler, "_handle_cancel") as mock_handle:

            async def mock_handle_func(*args, **kwargs):
                pass

            mock_handle.side_effect = mock_handle_func
            request = await handler.add_interrupt(subagent_id, "cancel")
            await handler._handle_interrupt(subagent_id, request)
            assert mock_handle.called

    @pytest.mark.asyncio
    async def test_handle_pause_interrupt(self, mock_manager):
        """Test handling pause interrupt."""
        handler = InterruptHandler(mock_manager)
        subagent_id = "test-1234"

        request = await handler.add_interrupt(subagent_id, "pause")
        await handler._handle_interrupt(subagent_id, request)
        assert subagent_id in handler._paused_subagents

    @pytest.mark.asyncio
    async def test_handle_resume_interrupt(self, mock_manager):
        """Test handling resume interrupt."""
        handler = InterruptHandler(mock_manager)
        subagent_id = "test-1234"
        handler._paused_subagents.add(subagent_id)

        request = await handler.add_interrupt(subagent_id, "resume")
        await handler._handle_interrupt(subagent_id, request)
        assert subagent_id not in handler._paused_subagents


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
