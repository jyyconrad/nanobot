"""Test command implementation."""

import subprocess
from typing import Any

from .base import Command


class TestCommand(Command):
    """测试命令"""

    @property
    def name(self) -> str:
        return "test"

    @property
    def description(self) -> str:
        return "Run complete testing pipeline"

    async def execute(self, context: dict[str, Any]) -> str:
        """执行测试管道"""
        results = []

        # 1. 类型检查
        try:
            subprocess.run(
                ["ruff", "check", "--select", "I"],
                check=True,
                capture_output=True,
                text=True,
            )
            results.append("✅ Type check passed")
        except subprocess.CalledProcessError as e:
            results.append(f"❌ Type check failed: {e.output}")

        # 2. Lint
        try:
            subprocess.run(
                ["ruff", "check", "."], check=True, capture_output=True, text=True
            )
            results.append("✅ Lint passed")
        except subprocess.CalledProcessError as e:
            results.append(f"❌ Lint failed: {e.output}")

        # 3. 运行测试
        try:
            subprocess.run(["pytest"], check=True, capture_output=True, text=True)
            results.append("✅ Tests passed")
        except subprocess.CalledProcessError as e:
            results.append(f"❌ Tests failed: {e.output}")

        return "\n".join(results)
