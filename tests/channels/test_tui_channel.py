"""Tests for TUI channel."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    config = Mock()
    config.prompt = "> "
    config.colors = True
    return config


@pytest.fixture
def mock_bus():
    """Create mock message bus."""
    bus = Mock()
    bus.publish_inbound = AsyncMock()
    return bus


@pytest.fixture
def tui_channel(mock_config, mock_bus):
    """Create TUI channel instance."""
    from nanobot.channels.tui_channel import TUIChannel
    return TUIChannel(mock_config, mock_bus)


class TestTUIChannel:
    """Tests for TUI channel."""

    def test_channel_initialization(self, tui_channel, mock_config):
        """Test channel initialization."""
        assert tui_channel.name == "tui"
        assert tui_channel.prompt == mock_config.prompt
        assert tui_channel.use_colors == mock_config.colors
        assert tui_channel.is_running is False



    @pytest.mark.asyncio
    async def test_send_message(self, tui_channel):
        """Test sending (displaying) a message."""
        from nanobot.bus.events import OutboundMessage

        outbound_msg = OutboundMessage(
            channel="tui",
            chat_id="tui",
            content="Hello, World!",
            sender_id="bot",
            media=[],
            metadata={}
        )

        # Should not raise, just display
        await tui_channel.send(outbound_msg)

    @pytest.mark.asyncio
    async def test_start_stop(self, tui_channel):
        """Test starting and stopping channel."""
        # Mock input to avoid blocking
        with patch.object(tui_channel, '_input_loop', new=AsyncMock()):
            await tui_channel.start()
            assert tui_channel.is_running is True

            await tui_channel.stop()
            assert tui_channel.is_running is False

    @pytest.mark.asyncio
    async def test_input_loop_exit_command(self, tui_channel, mock_bus):
        """Test input loop with exit command."""
        # Mock input to return exit command
        with patch.object(tui_channel, '_get_input_async', return_value=AsyncMock(return_value="exit")):
            await tui_channel._input_loop()

            # Should handle exit command gracefully
            assert tui_channel._session_active is False

    @pytest.mark.asyncio
    async def test_input_loop_regular_message(self, tui_channel, mock_bus):
        """Test input loop with regular message."""
        tui_channel._running = True

        # Mock input to return message then None to exit
        inputs = ["Hello, bot!", None]
        input_iter = iter(inputs)

        async def mock_input():
            try:
                return next(input_iter)
            except StopIteration:
                return None

        with patch.object(tui_channel, '_get_input_async', side_effect=mock_input):
            await asyncio.sleep(0.1)  # Let the loop run briefly
            tui_channel._running = False

        # Verify message was published
        mock_bus.publish_inbound.assert_called()
        inbound_msg = mock_bus.publish_inbound.call_args[0][0]
        assert inbound_msg.channel == "tui"
        assert inbound_msg.content == "Hello, bot!"

    @pytest.mark.asyncio
    async def test_get_input_async_timeout(self, tui_channel):
        """Test async input with timeout."""
        # Mock input to raise TimeoutError on first call, return input on second
        import asyncio
        with patch('select.select', return_value=([], [], [])):
            result = await tui_channel._get_input_async()
            assert result is None

    @pytest.mark.asyncio
    async def test_get_input_async_success(self, tui_channel):
        """Test successful async input."""
        import asyncio
        import select

        # Mock select to indicate data available
        with patch('select.select', return_value=([Mock()], [], [])):
            with patch('builtins.input', return_value="test input"):
                result = await tui_channel._get_input_async()
                assert result == "test input"

    def test_show_welcome(self, tui_channel):
        """Test displaying welcome message."""
        # Should not raise
        tui_channel.show_welcome()

    def test_clear_screen(self, tui_channel):
        """Test clearing screen."""
        # Should not raise
        tui_channel.clear_screen()

    def test_display_message_rich(self, tui_channel):
        """Test displaying message with rich formatting."""
        # Mock rich console
        tui_channel._rich_console = Mock()

        tui_channel._display_message("User", "Hello there!")
        tui_channel._rich_console.print.assert_called()

    def test_display_message_plain(self, tui_channel):
        """Test displaying message in plain text."""
        # Remove rich console
        tui_channel._rich_console = None

        # Mock print
        with patch('builtins.print') as mock_print:
            tui_channel._display_message("User", "Hello there!")
            mock_print.assert_called()

    def test_display_rich_message_colors_enabled(self, tui_channel):
        """Test rich message display with colors."""
        tui_channel._rich_console = Mock()
        tui_channel.use_colors = True

        tui_channel._display_rich_message("User", "Hello")
        tui_channel._rich_console.print.assert_called()

    def test_display_rich_message_colors_disabled(self, tui_channel):
        """Test rich message display without colors."""
        tui_channel._rich_console = Mock()
        tui_channel.use_colors = False

        tui_channel._display_rich_message("User", "Hello")
        tui_channel._rich_console.print.assert_called()

    def test_display_plain_message(self, tui_channel):
        """Test plain message display."""
        with patch('builtins.print') as mock_print:
            tui_channel._display_plain_message("User", "Hello")
            mock_print.assert_called_with("[User] Hello")

    @pytest.mark.asyncio
    async def test_input_loop_keyboard_interrupt(self, tui_channel):
        """Test input loop with keyboard interrupt."""
        # Mock input to raise KeyboardInterrupt
        with patch.object(tui_channel, '_get_input_async', side_effect=KeyboardInterrupt):
            await tui_channel._input_loop()

        # Should handle gracefully
        assert tui_channel._session_active is True

    @pytest.mark.asyncio
    async def test_input_loop_eof_error(self, tui_channel):
        """Test input loop with EOF error."""
        # Mock input to raise EOFError
        with patch.object(tui_channel, '_get_input_async', side_effect=EOFError):
            await tui_channel._input_loop()

        # Should handle gracefully
        assert tui_channel._session_active is True

    @pytest.mark.asyncio
    async def test_input_loop_exception(self, tui_channel):
        """Test input loop with unexpected exception."""
        tui_channel._running = True

        # Mock input to raise exception
        with patch.object(tui_channel, '_get_input_async', side_effect=Exception("Unexpected error")):
            await tui_channel._input_loop()

        # Should handle gracefully
