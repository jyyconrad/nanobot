"""Performance tests for Opencode commands system."""

import time

from nanobot.commands.registry import CommandRegistry


def test_command_parsing_performance():
    """Test command parsing performance."""
    registry = CommandRegistry()

    start = time.time()
    for i in range(1000):
        registry.parse_command(f"/test arg{i}")

    duration = time.time() - start
    assert duration < 0.1  # 1000 次解析在 100ms 内完成
