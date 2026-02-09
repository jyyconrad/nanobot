"""Command base class for Nanobot commands system."""

from abc import ABC, abstractmethod
from typing import Any


class Command(ABC):
    """命令基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """命令名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """命令描述"""
        pass

    @property
    def aliases(self) -> list[str]:
        """命令别名"""
        return []

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> str:
        """执行命令"""
        pass
