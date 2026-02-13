"""
测试新消息处理程序
"""

from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from nanobot.agent.decision.models import (
    DecisionRequest,
    DecisionResult,
    NewMessageRequest,
)
from nanobot.agent.decision.new_message_handler import NewMessageHandler
from nanobot.agent.loop import AgentLoop


class TestNewMessageHandler:
    """测试 NewMessageHandler 类"""

    @pytest.fixture
    def mock_agent_loop(self):
        """创建模拟的 AgentLoop"""
        mock = Mock(spec=AgentLoop)
        return mock

    @pytest.fixture
    def handler(self, mock_agent_loop):
        """创建新消息处理程序实例"""
        return NewMessageHandler(mock_agent_loop)

    @pytest.mark.asyncio
    async def test_initialization(self, handler, mock_agent_loop):
        """测试初始化"""
        assert handler is not None
        assert handler.agent_loop == mock_agent_loop

    @pytest.mark.asyncio
    async def test_handle_request_valid_message(self, handler):
        """测试处理有效消息请求"""
        request = DecisionRequest(
            request_type="new_message",
            data={
                "message_id": "msg123",
                "content": "请帮我查询天气",
                "sender_id": "user456",
                "timestamp": 1234567890,
                "conversation_id": "conv789",
            },
        )

        result = await handler.handle_request(request)
        assert result.success
        assert isinstance(result, DecisionResult)

    @pytest.mark.asyncio
    async def test_handle_request_invalid_data(self, handler):
        """测试处理无效数据请求"""
        request = DecisionRequest(
            request_type="new_message",
            data={},  # 缺少必填字段
        )

        result = await handler.handle_request(request)
        assert not result.success
        assert result.action == "error"

    @pytest.mark.asyncio
    async def test_handle_cancel_message(self, handler):
        """测试处理取消消息"""
        request = DecisionRequest(
            request_type="new_message",
            data={
                "message_id": "msg123",
                "content": "取消任务",
                "sender_id": "user456",
                "timestamp": 1234567890,
                "conversation_id": "conv789",
            },
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "cancel_task"

    @pytest.mark.asyncio
    async def test_handle_correction_message(self, handler):
        """测试处理修正消息"""
        request = DecisionRequest(
            request_type="new_message",
            data={
                "message_id": "msg123",
                "content": "不对，我要查的是明天的天气",
                "sender_id": "user456",
                "timestamp": 1234567890,
                "conversation_id": "conv789",
            },
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "handle_correction"

    @pytest.mark.asyncio
    async def test_handle_query_message(self, handler):
        """测试处理查询消息"""
        request = DecisionRequest(
            request_type="new_message",
            data={
                "message_id": "msg123",
                "content": "查一下今天的天气？",
                "sender_id": "user456",
                "timestamp": 1234567890,
                "conversation_id": "conv789",
            },
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "simple_query"

    @pytest.mark.asyncio
    async def test_handle_other_message(self, handler):
        """测试处理其他类型消息"""
        request = DecisionRequest(
            request_type="new_message",
            data={
                "message_id": "msg123",
                "content": "帮我创建一个待办事项",
                "sender_id": "user456",
                "timestamp": 1234567890,
                "conversation_id": "conv789",
            },
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "create_task"

    def test_new_message_request_validation(self):
        """测试新消息请求验证"""
        with pytest.raises(ValidationError):
            NewMessageRequest()

        valid_request = NewMessageRequest(
            message_id="msg123",
            content="测试消息",
            sender_id="user456",
            timestamp=1234567890,
            conversation_id="conv789",
        )
        assert valid_request.message_id == "msg123"
        assert valid_request.content == "测试消息"
        assert valid_request.sender_id == "user456"
        assert valid_request.conversation_id == "conv789"

    def test_new_message_request_with_type(self):
        """测试带类型的新消息请求"""
        request = NewMessageRequest(
            message_id="msg123",
            content="测试消息",
            sender_id="user456",
            timestamp=1234567890,
            conversation_id="conv789",
            message_type="image",
        )
        assert request.message_type == "image"

    @pytest.mark.asyncio
    async def test_should_create_task(self, handler):
        """测试是否应该创建任务的判断"""
        # 使用私有方法进行测试（实际生产代码中应该有公共方法）
        valid_message = NewMessageRequest(
            message_id="msg123",
            content="这是一个有效的任务请求",
            sender_id="user456",
            timestamp=1234567890,
            conversation_id="conv789",
        )

        invalid_message = NewMessageRequest(
            message_id="msg124",
            content="Hi",
            sender_id="user456",
            timestamp=1234567890,
            conversation_id="conv789",
        )

        # 由于 _should_create_task 是私有方法，我们使用特殊方式访问
        result1 = await handler._should_create_task(valid_message)
        result2 = await handler._should_create_task(invalid_message)

        assert result1 is True
        assert result2 is False

    @pytest.mark.asyncio
    async def test_extract_intent(self, handler):
        """测试意图提取"""
        help_message = NewMessageRequest(
            message_id="msg123",
            content="帮助",
            sender_id="user456",
            timestamp=1234567890,
            conversation_id="conv789",
        )

        query_message = NewMessageRequest(
            message_id="msg124",
            content="查询天气",
            sender_id="user456",
            timestamp=1234567890,
            conversation_id="conv789",
        )

        create_message = NewMessageRequest(
            message_id="msg125",
            content="创建任务",
            sender_id="user456",
            timestamp=1234567890,
            conversation_id="conv789",
        )

        intent1 = await handler._extract_intent(help_message)
        intent2 = await handler._extract_intent(query_message)
        intent3 = await handler._extract_intent(create_message)

        assert intent1 == "help"
        assert intent2 == "query"
        assert intent3 == "create"
