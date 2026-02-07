"""
Message router for Nanobot - classifies and routes messages to appropriate handlers.
"""

from typing import Dict

from .models import MessageCategory


class MessageRouter:
    """
    Message router that classifies messages into categories and routes them to handlers.
    """

    def __init__(self, llm_provider=None):
        self.llm_provider = llm_provider
        self._category_cache: Dict[str, MessageCategory] = {}
        self._category_rules = self._create_category_rules()

    def _create_category_rules(self) -> Dict[MessageCategory, list]:
        """Create category classification rules."""
        return {
            MessageCategory.TASK_CREATE: [
                "创建任务",
                "新建任务",
                "开始任务",
                "任务创建",
            ],
            MessageCategory.TASK_STATUS: [
                "查看任务",
                "任务状态",
                "查询任务",
                "任务进度",
            ],
            MessageCategory.TASK_CANCEL: [
                "取消任务",
                "终止任务",
                "停止任务",
            ],
            MessageCategory.TASK_COMPLETE: [
                "完成任务",
                "任务完成",
                "结束任务",
            ],
            MessageCategory.TASK_LIST: [
                "列出任务",
                "任务列表",
                "所有任务",
            ],
            MessageCategory.HELP: [
                "帮助",
                "使用说明",
                "帮我",
                "怎么用",
            ],
            MessageCategory.CONTROL: [
                "重试",
                "继续",
                "暂停",
                "恢复",
                "控制",
            ],
            MessageCategory.INQUIRY: [
                "查询",
                "什么是",
                "如何",
                "为什么",
                "怎么样",
            ],
            MessageCategory.CHAT: [
                "你好",
                "哈喽",
                "聊天",
                "随便说",
            ],
        }

    def get_category(self, message: str) -> MessageCategory:
        """
        Classify a message into a category.

        Args:
            message: The message to classify

        Returns:
            MessageCategory: The classified category
        """
        # Check cache
        if message in self._category_cache:
            return self._category_cache[message]

        # Classify using rules
        category = self._classify_with_rules(message)

        # Cache the result
        self._category_cache[message] = category

        return category

    def _classify_with_rules(self, message: str) -> MessageCategory:
        """Classify message using predefined rules."""
        message_lower = message.lower()

        for category, keywords in self._category_rules.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return category

        # Default to unknown if no category matches
        return MessageCategory.UNKNOWN

    async def route(self, message: str, context: Dict) -> MessageCategory:
        """
        Route message to appropriate category (async version).

        Args:
            message: The message to route
            context: Additional context for classification

        Returns:
            MessageCategory: The classified category
        """
        return self.get_category(message)

    async def get_category_hint(self, message: str) -> str:
        """
        Get a hint about how the message would be classified.

        Args:
            message: The message to analyze

        Returns:
            str: Classification hint
        """
        category = self.get_category(message)
        return f"Message classified as: {category.value} ({category.name})"
