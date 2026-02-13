"""Message routing strategies for Nanobot channels."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional


class RoutePriority(Enum):
    """Message routing priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RouteStrategy(ABC):
    """Base class for message routing strategies."""

    @abstractmethod
    def route(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Determine the routing target for a message.

        Args:
            message: The incoming message with metadata

        Returns:
            The target handler/function name, or None if no match
        """
        pass

    @abstractmethod
    def get_priority(self, message: Dict[str, Any]) -> RoutePriority:
        """
        Get the routing priority for a message.

        Args:
            message: The incoming message

        Returns:
            The routing priority level
        """
        pass


class FeishuRouteStrategy(RouteStrategy):
    """Routing strategy for Feishu messages."""

    def __init__(self):
        self.private_chat_handler = "handle_private_chat"
        self.group_chat_handler = "handle_group_chat"
        self.mention_handler = "handle_mention"
        self.command_handler = "handle_command"

    def route(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Route Feishu messages based on chat type and content.

        Args:
            message: Feishu message dict with 'chat_type' and 'content'

        Returns:
            The appropriate handler name
        """
        chat_type = message.get("chat_type")
        content = message.get("content", "")

        # Command messages (start with /)
        if content.startswith("/"):
            return self.command_handler

        # Group chat
        if chat_type == "group":
            # Check for @mention
            if self._is_mentioned(message):
                return self.mention_handler
            return self.group_chat_handler

        # Private chat
        if chat_type == "private":
            return self.private_chat_handler

        return None

    def get_priority(self, message: Dict[str, Any]) -> RoutePriority:
        """
        Get routing priority for Feishu messages.

        Priority order:
        - HIGH: Commands, @mentions in group chats
        - MEDIUM: Private chats
        - LOW: Regular group chats
        """
        chat_type = message.get("chat_type")
        content = message.get("content", "")

        if content.startswith("/"):
            return RoutePriority.HIGH

        if chat_type == "group" and self._is_mentioned(message):
            return RoutePriority.HIGH

        if chat_type == "private":
            return RoutePriority.MEDIUM

        return RoutePriority.LOW

    def _is_mentioned(self, message: Dict[str, Any]) -> bool:
        """Check if the message mentions the bot."""
        mentions = message.get("mentions", [])
        bot_id = message.get("bot_id")
        return bot_id in mentions


class WebChatRouteStrategy(RouteStrategy):
    """Routing strategy for WebChat messages."""

    def __init__(self):
        self.chat_handler = "handle_chat"
        self.command_handler = "handle_command"
        self.feedback_handler = "handle_feedback"

    def route(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Route WebChat messages based on message type.

        Args:
            message: WebChat message dict with 'type' or content

        Returns:
            The appropriate handler name
        """
        message_type = message.get("type", "chat")
        content = message.get("content", "")

        if message_type == "command" or content.startswith("/"):
            return self.command_handler

        if message_type == "feedback":
            return self.feedback_handler

        if message_type == "chat":
            return self.chat_handler

        return None

    def get_priority(self, message: Dict[str, Any]) -> RoutePriority:
        """
        Get routing priority for WebChat messages.

        Priority order:
        - HIGH: Commands
        - MEDIUM: Feedback
        - LOW: Regular chat
        """
        message_type = message.get("type", "chat")
        content = message.get("content", "")

        if message_type == "command" or content.startswith("/"):
            return RoutePriority.HIGH

        if message_type == "feedback":
            return RoutePriority.MEDIUM

        return RoutePriority.LOW


class TUIRouteStrategy(RouteStrategy):
    """Routing strategy for TUI (Text User Interface) messages."""

    def __init__(self):
        self.chat_handler = "handle_chat"
        self.command_handler = "handle_command"
        self.exit_handler = "handle_exit"

    def route(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Route TUI messages based on content.

        Args:
            message: TUI message dict with 'content'

        Returns:
            The appropriate handler name
        """
        content = message.get("content", "").strip().lower()

        # Exit commands
        if content in ("exit", "quit", "q"):
            return self.exit_handler

        # Command messages (start with /)
        if content.startswith("/"):
            return self.command_handler

        # Regular chat
        return self.chat_handler

    def get_priority(self, message: Dict[str, Any]) -> RoutePriority:
        """
        Get routing priority for TUI messages.

        Priority order:
        - HIGH: Commands and exit commands
        - LOW: Regular chat
        """
        content = message.get("content", "").strip().lower()

        if content.startswith("/") or content in ("exit", "quit", "q"):
            return RoutePriority.HIGH

        return RoutePriority.LOW
