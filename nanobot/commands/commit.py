"""Git commit command implementation."""

import subprocess
from typing import Any

from .base import Command
from .test import TestCommand


class CommitCommand(Command):
    """Git 提交命令"""

    @property
    def name(self) -> str:
        return "commit"

    @property
    def description(self) -> str:
        return "Create well-formatted git commits"

    async def execute(self, context: dict[str, Any]) -> str:
        """执行 git 提交"""
        # 1. 运行测试
        test_cmd = TestCommand()
        test_result = await test_cmd.execute(context)
        if "❌" in test_result:
            return f"Tests failed, cannot commit:\n{test_result}"

        # 2. 分析 git 状态
        status = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True
        ).stdout

        if not status.strip():
            return "No changes to commit"

        # 4. 生成提交消息
        message = "Auto-commit from Nanobot"

        # 5. 执行提交
        subprocess.run(["git", "commit", "-m", message])

        return f"✅ Committed: {message[:50]}..."
