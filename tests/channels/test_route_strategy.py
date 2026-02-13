"""Tests for message routing strategies."""

import pytest
from nanobot.channels.route_strategy import (
    RouteStrategy,
    FeishuRouteStrategy,
    WebChatRouteStrategy,
    TUIRouteStrategy,
    RoutePriority
)


class TestFeishuRouteStrategy:
    """Tests for Feishu routing strategy."""

    def setup_method(self):
        """Setup test fixtures."""
        self.strategy = FeishuRouteStrategy()

    def test_private_chat_routing(self):
        """Test private chat messages are routed correctly."""
        message = {
            "chat_type": "private",
            "content": "Hello",
            "bot_id": "ou_bot001"
        }

        handler = self.strategy.route(message)
        assert handler == self.strategy.private_chat_handler

    def test_group_chat_routing(self):
        """Test group chat messages are routed correctly."""
        message = {
            "chat_type": "group",
            "content": "Hello everyone",
            "bot_id": "ou_bot001",
            "mentions": []
        }

        handler = self.strategy.route(message)
        assert handler == self.strategy.group_chat_handler

    def test_group_mention_routing(self):
        """Test @mention in group chat is routed correctly."""
        message = {
            "chat_type": "group",
            "content": "@openclaw help me",
            "bot_id": "ou_bot001",
            "mentions": ["ou_bot001"]
        }

        handler = self.strategy.route(message)
        assert handler == self.strategy.mention_handler

    def test_command_routing(self):
        """Test command messages are routed correctly."""
        message = {
            "chat_type": "private",
            "content": "/status",
            "bot_id": "ou_bot001"
        }

        handler = self.strategy.route(message)
        assert handler == self.strategy.command_handler

    def test_command_priority(self):
        """Test commands get high priority."""
        message = {
            "chat_type": "private",
            "content": "/status",
            "bot_id": "ou_bot001"
        }

        priority = self.strategy.get_priority(message)
        assert priority == RoutePriority.HIGH

    def test_mention_priority(self):
        """Test @mentions get high priority."""
        message = {
            "chat_type": "group",
            "content": "@openclaw help",
            "bot_id": "ou_bot001",
            "mentions": ["ou_bot001"]
        }

        priority = self.strategy.get_priority(message)
        assert priority == RoutePriority.HIGH

    def test_private_chat_priority(self):
        """Test private chats get medium priority."""
        message = {
            "chat_type": "private",
            "content": "Hello",
            "bot_id": "ou_bot001"
        }

        priority = self.strategy.get_priority(message)
        assert priority == RoutePriority.MEDIUM

    def test_group_chat_priority(self) -> None:
        """Test regular group chats get low priority."""
        message = {
            "chat_type": "group",
            "content": "Hello everyone",
            "bot_id": "ou_bot001",
            "mentions": []
        }

        priority = self.strategy.get_priority(message)
        assert priority == RoutePriority.LOW


class TestWebChatRouteStrategy:
    """Tests for WebChat routing strategy."""

    def setup_method(self):
        """Setup test fixtures."""
        self.strategy = WebChatRouteStrategy()

    def test_chat_routing(self):
        """Test chat messages are routed correctly."""
        message = {
            "type": "chat",
            "content": "Hello"
        }

        handler = self.strategy.route(message)
        assert handler == self.strategy.chat_handler

    def test_command_routing(self):
        """Test command messages are routed correctly."""
        message = {
            "type": "chat",
            "content": "/help"
        }

        handler = self.strategy.route(message)
        assert handler == self.strategy.command_handler

    def test_feedback_routing(self):
        """Test feedback messages are routed correctly."""
        message = {
            "type": "feedback",
            "content": "Great!"
        }

        handler = self.strategy.route(message)
        assert handler == self.strategy.feedback_handler

    def test_command_priority(self):
        """Test commands get high priority."""
        message = {
            "type": "chat",
            "content": "/help"
        }

        priority = self.strategy.get_priority(message)
        assert priority == RoutePriority.HIGH

    def test_feedback_priority(self):
        """Test feedback gets medium priority."""
        message = {
            "type": "feedback",
            "content": "Great!"
        }

        priority = self.strategy.get_priority(message)
        assert priority == RoutePriority.MEDIUM

    def test_chat_priority(self):
        """Test regular chat gets low priority."""
        message = {
            "type": "chat",
            "content": "Hello"
        }

        priority = self.strategy.get_priority(message)
        assert priority == RoutePriority.LOW


class TestTUIRouteStrategy:
    """Tests for TUI routing strategy."""

    def setup_method(self):
        """Setup test fixtures."""
        self.strategy = TUIRouteStrategy()

    def test_chat_routing(self):
        """Test chat messages are routed correctly."""
        message = {
            "content": "Hello"
        }

        handler = self.strategy.route(message)
        assert handler == self.strategy.chat_handler

    def test_command_routing(self):
        """Test command messages are routed correctly."""
        message = {
            "content": "/help"
        }

        handler = self.strategy.route(message)
        assert handler == self.strategy.command_handler

    def test_exit_routing(self):
        """Test exit commands are routed correctly."""
        for cmd in ["exit", "quit", "q"]:
            message = {"content": cmd}
            handler = self.strategy.route(message)
            assert handler == self.strategy.exit_handler

    def test_command_priority(self):
        """Test commands get high priority."""
        message = {
            "content": "/help"
        }

        priority = self.strategy.get_priority(message)
        assert priority == RoutePriority.HIGH

    def test_exit_priority(self):
        """Test exit commands get high priority."""
        for cmd in ["exit", "quit", "q"]:
            message = {"content": cmd}
            priority = self.strategy.get_priority(message)
            assert priority == RoutePriority.HIGH

    def test_chat_priority(self):
        """Test regular chat gets low priority."""
        message = {
            "content": "Hello"
        }

        priority = self.strategy.get_priority(message)
        assert priority == RoutePriority.LOW

    def test_whitespace_handling(self):
        """Test whitespace in content is handled correctly."""
        message = {
            "content": "  /help  "  # Extra whitespace
        }

        handler = self.strategy.route(message)
        assert handler == self.strategy.command_handler

    def test_case_insensitive_exit(self):
        """Test exit commands are case insensitive."""
        for cmd in ["EXIT", "Quit", "Q", "exit", "quit", "q"]:
            message = {"content": cmd}
            handler = self.strategy.route(message)
            assert handler == self.strategy.exit_handler
