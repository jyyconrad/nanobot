"""
Tests for MessageRouter.
"""

import pytest

from nanobot.agent.workflow.message_router import MessageRouter
from nanobot.agent.workflow.models import MessageCategory


class TestMessageRouter:
    """Tests for MessageRouter class."""

    def setup_method(self):
        """Setup method to create a new instance for each test."""
        self.router = MessageRouter()

    def test_initialization(self):
        """Test that MessageRouter initializes correctly."""
        assert self.router is not None
        assert hasattr(self.router, "get_category")
        assert hasattr(self.router, "route")
        assert hasattr(self.router, "_classify_with_rules")

    def test_classify_task_create_message(self):
        """Test classification of task creation messages."""
        test_messages = [
            "创建任务",
            "新建任务",
            "开始任务",
            "任务创建",
        ]

        for message in test_messages:
            category = self.router.get_category(message)
            assert category == MessageCategory.TASK_CREATE

    def test_classify_task_status_message(self):
        """Test classification of task status messages."""
        test_messages = [
            "查看任务",
            "任务状态",
            "查询任务",
            "任务进度",
        ]

        for message in test_messages:
            category = self.router.get_category(message)
            assert category == MessageCategory.TASK_STATUS

    def test_classify_task_cancel_message(self):
        """Test classification of task cancel messages."""
        test_messages = [
            "取消任务",
            "终止任务",
            "停止任务",
        ]

        for message in test_messages:
            category = self.router.get_category(message)
            assert category == MessageCategory.TASK_CANCEL

    def test_classify_task_complete_message(self):
        """Test classification of task complete messages."""
        test_messages = [
            "完成任务",
            "任务完成",
            "结束任务",
        ]

        for message in test_messages:
            category = self.router.get_category(message)
            assert category == MessageCategory.TASK_COMPLETE

    def test_classify_task_list_message(self):
        """Test classification of task list messages."""
        test_messages = [
            "列出任务",
            "任务列表",
            "所有任务",
        ]

        for message in test_messages:
            category = self.router.get_category(message)
            assert category == MessageCategory.TASK_LIST

    def test_classify_help_message(self):
        """Test classification of help messages."""
        test_messages = [
            "帮助",
            "使用说明",
            "帮我",
            "怎么用",
        ]

        for message in test_messages:
            category = self.router.get_category(message)
            assert category == MessageCategory.HELP

    def test_classify_control_message(self):
        """Test classification of control messages."""
        test_messages = [
            "重试",
            "继续",
            "暂停",
            "恢复",
            "控制",
        ]

        for message in test_messages:
            category = self.router.get_category(message)
            assert category == MessageCategory.CONTROL

    def test_classify_inquiry_message(self):
        """Test classification of inquiry messages."""
        test_messages = [
            "查询",
            "什么是",
            "如何",
            "为什么",
            "怎么样",
        ]

        for message in test_messages:
            category = self.router.get_category(message)
            assert category == MessageCategory.INQUIRY

    def test_classify_chat_message(self):
        """Test classification of chat messages."""
        test_messages = [
            "你好",
            "哈喽",
            "聊天",
            "随便说",
        ]

        for message in test_messages:
            category = self.router.get_category(message)
            assert category == MessageCategory.CHAT

    def test_classify_unknown_message(self):
        """Test classification of unknown messages."""
        test_messages = [
            "这是一个未知的消息类型",
            "Random text without any keywords",
            "123456",
        ]

        for message in test_messages:
            category = self.router.get_category(message)
            assert category == MessageCategory.UNKNOWN

    def test_message_cache(self):
        """Test that message classification results are cached."""
        message = "测试消息分类缓存"
        category1 = self.router.get_category(message)

        # 修改内部规则（不推荐在实际代码中这样做，但用于测试）
        original_rules = self.router._category_rules
        self.router._category_rules = {MessageCategory.UNKNOWN: []}

        # 使用缓存的结果，而不是重新分类
        category2 = self.router.get_category(message)

        # 恢复原始规则
        self.router._category_rules = original_rules

        assert category1 == category2

    @pytest.mark.asyncio
    async def test_async_route(self):
        """Test the async route method."""
        message = "创建任务"
        category = await self.router.route(message, context={})
        assert category == MessageCategory.TASK_CREATE

    @pytest.mark.asyncio
    async def test_get_category_hint(self):
        """Test getting category hint."""
        message = "创建任务"
        hint = await self.router.get_category_hint(message)
        assert "Message classified as: task_create (TASK_CREATE)" in hint
