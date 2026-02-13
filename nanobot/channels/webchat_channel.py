"""WebChat channel implementation for Nanobot."""

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, Optional

from loguru import logger

from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus


class WebChatChannel:
    """
    WebChat channel for real-time web-based chat.

    Features:
    - WebSocket-based real-time communication
    - User authentication
    - Message format conversion
    - Session management
    """

    name = "webchat"

    def __init__(self, config: Any, bus: MessageBus):
        """
        Initialize WebChat channel.

        Args:
            config: Configuration object with ws_url, api_key, timeout attributes
            bus: Message bus for communication
        """
        self.config = config
        self.bus = bus
        self.ws_url = getattr(config, "ws_url", "ws://localhost:8000/ws")
        self.api_key = getattr(config, "api_key", "")
        self.timeout = getattr(config, "timeout", 30)
        self._running = False
        self._ws_connection = None
        self._authenticated = False
        self._user_cache: Dict[str, Dict[str, Any]] = {}
        self._receive_task = None

    async def start(self) -> None:
        """Start the WebChat channel and begin listening for messages."""
        if self._running:
            return

        self._running = True

        # Establish WebSocket connection
        if not await self.connect():
            logger.error("Failed to connect to WebChat server")
            self._running = False
            return

        # Start receiving messages
        self._receive_task = asyncio.create_task(self._message_loop())

        logger.info("WebChat channel started")

    async def stop(self) -> None:
        """Stop the WebChat channel."""
        self._running = False

        # Stop receiving task
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        # Disconnect
        await self.disconnect()

        logger.info("WebChat channel stopped")

    async def send(self, msg: OutboundMessage) -> None:
        """
        Send a message through WebChat.

        Args:
            msg: Outbound message to send
        """
        if not self._running or not self._ws_connection:
            logger.error("WebChat channel not running")
            return

        try:
            # Convert to WebChat format
            webchat_msg = {
                "type": "text",
                "from": "bot",
                "to": msg.chat_id,
                "content": msg.content,
                "timestamp": msg.timestamp or asyncio.get_event_loop().time(),
                "metadata": msg.metadata
            }

            await self._ws_connection.send(json.dumps(webchat_msg))
            logger.debug(f"WebChat message sent to {msg.chat_id}")

        except Exception as e:
            logger.error(f"Failed to send WebChat message: {e}")

    async def connect(self) -> bool:
        """
        Establish WebSocket connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            from websockets import connect

            self._ws_connection = await connect(
                self.ws_url,
                close_timeout=self.timeout
            )
            logger.info(f"WebChat connected to {self.ws_url}")
            return True

        except ImportError:
            logger.error("websockets library not installed. Run: pip install websockets")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to WebChat: {e}")
            return False

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self._ws_connection:
            await self._ws_connection.close()
            self._ws_connection = None
            self._authenticated = False
            logger.info("WebChat disconnected")

    async def _message_loop(self) -> None:
        """Main message receiving loop."""
        try:
            async for raw_msg in self._ws_connection:
                if not self._running:
                    break

                try:
                    webchat_msg = json.loads(raw_msg)
                    await self._handle_incoming_message(webchat_msg)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse WebChat message: {e}")

        except Exception as e:
            if self._running:
                logger.error(f"Error in WebChat message loop: {e}")

    async def _handle_incoming_message(self, webchat_msg: Dict[str, Any]) -> None:
        """
        Handle incoming message from WebChat.

        Args:
            webchat_msg: Message in WebChat format
        """
        try:
            # Convert to internal format
            sender_id = webchat_msg.get("from", "unknown")
            content = webchat_msg.get("content", "")
            metadata = {
                "message_id": webchat_msg.get("id"),
                "message_type": webchat_msg.get("type", "text")
            }

            # Check permissions
            if not self.is_allowed(sender_id):
                logger.warning(f"WebChat message from unauthorized user: {sender_id}")
                return

            # Create inbound message
            inbound_msg = InboundMessage(
                channel=self.name,
                sender_id=sender_id,
                chat_id=sender_id,  # WebChat uses same ID for user and chat
                content=content,
                media=[],
                metadata=metadata
            )

            # Publish to message bus
            await self.bus.publish_inbound(inbound_msg)

        except Exception as e:
            logger.error(f"Error handling WebChat message: {e}")

    def is_allowed(self, sender_id: str) -> bool:
        """
        Check if a sender is allowed to use this bot.

        Args:
            sender_id: The sender's identifier.

        Returns:
            True if allowed, False otherwise.
        """
        allow_list = getattr(self.config, "allow_from", [])

        # If no allow list, allow everyone
        if not allow_list:
            return True

        sender_str = str(sender_id)
        if sender_str in allow_list:
            return True
        if "|" in sender_str:
            for part in sender_str.split("|"):
                if part and part in allow_list:
                    return True
        return False

    async def authenticate_user(self, user_id: str, token: str) -> bool:
        """
        Authenticate a user.

        Args:
            user_id: User ID
            token: Authentication token

        Returns:
            True if authenticated, False otherwise
        """
        # In production, this would validate against an auth service
        # For now, simple token check
        if token == self.api_key:
            self._authenticated = True
            self._user_cache[user_id] = {"authenticated": True}
            logger.info(f"User {user_id} authenticated")
            return True

        return False

    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached user information.

        Args:
            user_id: User ID

        Returns:
            User info dict or None if not found
        """
        return self._user_cache.get(user_id)

    @property
    def is_running(self) -> bool:
        """Check if the channel is running."""
        return self._running
