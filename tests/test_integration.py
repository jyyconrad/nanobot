"""Integration tests for Opencode commands system."""

import pytest

from nanobot.commands.registry import CommandRegistry


@pytest.mark.asyncio
async def test_command_registry():
    """Test that command registry loads all commands."""
    registry = CommandRegistry()

    # Check all commands are registered
    assert registry.get("review") is not None
    assert registry.get("optimize") is not None
    assert registry.get("test") is not None
    assert registry.get("commit") is not None
    assert registry.get("fix") is not None
    assert registry.get("debug") is not None

    # Check aliases
    assert registry.get("code-review") is not None
    assert registry.get("cr") is not None


@pytest.mark.asyncio
async def test_command_parsing():
    """Test command parsing."""
    registry = CommandRegistry()

    # Test valid commands
    name, args = registry.parse_command("/review")
    assert name == "review"
    assert args["raw"] == ""

    name, args = registry.parse_command("/test nanobot/")
    assert name == "test"
    assert args["raw"] == "nanobot/"


@pytest.mark.asyncio
async def test_invalid_command():
    """Test parsing invalid command."""
    registry = CommandRegistry()
    command = registry.get("invalid-command")
    assert command is None
