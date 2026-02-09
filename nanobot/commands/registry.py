"""Command registry for Nanobot commands system."""

from typing import Any

from .base import Command


class CommandRegistry:
    """命令注册表"""

    def __init__(self):
        self._commands: dict[str, Command] = {}
        self._register_builtin_commands()

    def _register_builtin_commands(self):
        """注册内置命令"""
        from .commit import CommitCommand
        from .debug import DebugCommand
        from .fix import FixCommand
        from .optimize import OptimizeCommand
        from .review import ReviewCommand
        from .test import TestCommand

        self.register(ReviewCommand())
        self.register(OptimizeCommand())
        self.register(TestCommand())
        self.register(CommitCommand())
        self.register(FixCommand())
        self.register(DebugCommand())

    def register(self, command: Command):
        """注册命令"""
        self._commands[command.name] = command
        for alias in command.aliases:
            self._commands[alias] = command

    def get(self, name: str) -> Command | None:
        """获取命令"""
        return self._commands.get(name)

    def parse_command(self, message: str) -> tuple[str | None, dict[str, Any]]:
        """解析命令"""
        if not message.startswith("/"):
            return None, {}

        parts = message[1:].split(maxsplit=1)
        command_name = parts[0]
        args_str = parts[1] if len(parts) > 1 else ""

        return command_name, {"raw": args_str}
