"""Tests for WebChat channel."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    config = Mock()
    config.ws_url = "ws://localhost:8000/ws"
    config.api_key = "test-api-key"
    config.timeout = 30
    config.allow_from = []
    return config


@pytest.fixture
def mock_bus():
    """Create mock message bus."""
    bus = Mock()
    bus.publish_inbound = AsyncMock()
    return bus


@pytest.fixture
def webchat_channel(mock_config, mock_bus):
    """Create WebChat channel instance."""
    from nanobot.channels.webchat_channel import WebChatChannel
    return WebChatChannel(mock_config, mock_bus)


class TestWebChatChannel:
    """Tests for WebChat channel."""

    def test_channel_initialization(self, webchat_channel, mock_config, mock_bus):
        """Test channel initialization."""
        assert webchat_channel.name == "webchat"
        assert webchat_channel.ws_url == mock_config.ws_url
        assert webchat_channel.api_key == mock_config.api_key
        assert webchat_channel.timeout == mock_config.timeout
        assert webchat_channel.is_running is False

    @pytest.mark.asyncio
    async def test_connect_success(self, webchat_channel):
        """Test successful WebSocket connection."""
        with patch("nanobot.channels.webchat_channel.connect") as mock_connect:
            # Mock WebSocket connection
            mock_ws = AsyncMock()
            mock_ws.send = AsyncMock()
            mock_connect.return_value = mock_ws

            result = await webchat_channel.connect()
            assert result is True

    @pytest.mark.asyncio
    async def test_connect_failure(self, webchat_channel):
        """Test failed WebSocket connection."""
        with patch("nanobot.channels.webchat_channel.connect") as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")

            result = await webchat_channel.connect()
            assert result is False

    @pytest.mark.asyncio
    async def test_send_message(self, webchat_channel, mock_bus):
        """Test sending a message."""
        from nanobot.bus.events import OutboundMessage

        # Mock WebSocket connection
        mock_ws = AsyncMock()
        webchat_channel._ws_connection = mock_ws
        webchat_channel._running = True

        # Create outbound message
        outbound_msg = OutboundMessage(
            channel="webchat",
            chat_id="user123",
            content="Hello, World!",
            sender_id="bot",
            media=[],
            metadata={}
        )

        await webchat_channel.send(outbound_msg)

        # Verify message was sent
        mock_ws.send.assert_called_once()
        sent_data = json.loads(mock_ws.send.call_args[0][0])
        assert sent_data["to"] == "user123"
        assert sent_data["content"] == "Hello, World!"

    @pytest.mark.asyncio
    async def test_send_message_not_running(self, webchat_channel):
        """Test sending message when channel is not running."""
        from nanobot.bus.events import OutboundMessage

        outbound_msg = OutboundMessage(
            channel="webchat",
            chat_id="user123",
            content="Hello",
            sender_id="bot",
            media=[],
            metadata={}
        )

        # Should not raise, just log error
        await webchat_channel.send(outbound_msg)

    @pytest.mark.asyncio
    async def test_handle_incoming_message(self, webchat_channel, mock_bus):
        """Test handling incoming message."""
        webchat_msg = {
            "id": "msg123",
            "from": "user456",
            "type": "text",
            "content": "Test message",
            "timestamp": 1234567890.0,
            "metadata": {}
        }

        await webchat_channel._handle_incoming_message(webchat_msg)

        # Verify message was published
        mock_bus.publish_inbound.assert_called_once()
        inbound_msg = mock_bus.publish_inbound.call_args[0][0]
        assert inbound_msg.channel == "webchat"
        assert inbound_msg.sender_id == "user456"
        assert inbound_msg.content == "Test message"

    @pytest.mark.asyncio
    async def test_handle_incoming_message_unauthorized(self, webchat_channel, mock_bus, mock_config):
        """Test handling message from unauthorized user."""
        mock_config.allow_from = ["user123"]

        webchat_msg = {
            "from": "user456",  # Not in allow list
            "content": "Test"
        }

        await webchat_channel._handle_incoming_message(webchat_msg)

        # Should not publish message
        mock_bus.publish_inbound.assert_not_called()

    def test_is_allowed(self, webchat_channel, mock_config):
        """Test permission checking."""
        # No allow list - allow everyone
        assert webchat_channel.is_allowed("user123") is True

        # With allow list
        mock_config.allow_from = ["user123", "user456"]
        assert webchat_channel.is_allowed("user123") is True
        assert webchat_channel.is_allowed("user999") is False

        # Pipe-separated IDs
        mock_config.allow_from = ["user123"]
        assert webchat_channel.is_allowed("user123|other") is True

    def test_authenticate_user(self, webchat_channel, mock_config):
        """Test user authentication."""
        # Valid token
        result = webchat_channel.authenticate_user("user123", "test-api-key")
        assert result is True
        assert webchat_channel._authenticated is True

        # Invalid token
        result = webchat_channel.authenticate_user("user456", "wrong-token")
        assert result is False

    def test_get_user_info(self, webchat_channel):
        """Test getting cached user info."""
        # No cached info
        assert webchat_channel.get_user_info("user123") is None

        # Add cached info
        webchat_channel._user_cache["user123"] = {"authenticated": True}
        result = webchat_channel.get_user_info("user123")
        assert result is not None
        assert result["authenticated"] is True

    @pytest.mark.asyncio
    async def test_disconnect(self, webchat_channel):
        """Test disconnecting."""
        mock_ws = AsyncMock()
        webchat_channel._ws_connection = mock_ws
        webchat_channel._authenticated = True

        await webchat_channel.disconnect()

        mock_ws.close.assert_called_once()
        assert webchat_channel._ws_connection is None
        assert webchat_channel._authenticated is False

    @pytest.mark.asyncio
    async def test_start_stop(self, webchat_channel):
        """Test starting and stopping the channel."""
        with patch.object(webchat_channel, 'connect', return_value=AsyncMock(return_value=True)):
            # Mock connect to return True
            webchat_channel.connect = AsyncMock(return_value=True)

            await webchat_channel.start()
            assert webchat_channel.is_running is True

            await webchat_channel.stop()
            assert webchat_channel.is_running is False
