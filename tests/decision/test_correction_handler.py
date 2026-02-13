"""
测试修正处理程序
"""

from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from nanobot.agent.decision.correction_handler import CorrectionHandler
from nanobot.agent.decision.models import (
    CorrectionRequest,
    DecisionRequest,
    DecisionResult,
)
from nanobot.agent.loop import AgentLoop
from nanobot.agent.task import Task


class TestCorrectionHandler:
    """测试 CorrectionHandler 类"""

    @pytest.fixture
    def mock_agent_loop(self):
        """创建模拟的 AgentLoop"""
        mock = Mock(spec=AgentLoop)
        return mock

    @pytest.fixture
    def handler(self, mock_agent_loop):
        """创建修正处理程序实例"""
        return CorrectionHandler(mock_agent_loop)

    @pytest.fixture
    def mock_task(self):
        """创建模拟的任务"""
        mock_task = Mock(spec=Task)
        mock_task.id = "task123"
        mock_task.status = "running"
        return mock_task

    @pytest.mark.asyncio
    async def test_initialization(self, handler, mock_agent_loop):
        """测试初始化"""
        assert handler is not None
        assert handler.agent_loop == mock_agent_loop

    @pytest.mark.asyncio
    async def test_handle_request_valid_correction(self, handler, mock_task):
        """测试处理有效修正请求"""
        request = DecisionRequest(
            request_type="correction",
            data={
                "message_id": "msg123",
                "correction": "修正内容",
                "task_id": "task123",
            },
            task=mock_task,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert isinstance(result, DecisionResult)

    @pytest.mark.asyncio
    async def test_handle_request_invalid_data(self, handler):
        """测试处理无效数据请求"""
        request = DecisionRequest(
            request_type="correction",
            data={},  # 缺少必填字段
        )

        result = await handler.handle_request(request)
        assert not result.success
        assert result.action == "error"

    @pytest.mark.asyncio
    async def test_handle_task_correction_running(self, handler, mock_task):
        """测试处理正在运行的任务修正"""
        mock_task.status = "running"

        request = DecisionRequest(
            request_type="correction",
            data={
                "message_id": "msg123",
                "correction": "修改任务参数",
                "task_id": "task123",
            },
            task=mock_task,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "update_task"

    @pytest.mark.asyncio
    async def test_handle_task_correction_completed(self, handler, mock_task):
        """测试处理已完成的任务修正"""
        mock_task.status = "completed"

        request = DecisionRequest(
            request_type="correction",
            data={
                "message_id": "msg123",
                "correction": "重新执行任务",
                "task_id": "task123",
            },
            task=mock_task,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "reopen_task"

    @pytest.mark.asyncio
    async def test_handle_task_correction_failed(self, handler, mock_task):
        """测试处理失败的任务修正"""
        mock_task.status = "failed"

        request = DecisionRequest(
            request_type="correction",
            data={
                "message_id": "msg123",
                "correction": "重新执行任务",
                "task_id": "task123",
            },
            task=mock_task,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "reopen_task"

    @pytest.mark.asyncio
    async def test_handle_message_correction(self, handler):
        """测试处理消息修正"""
        request = DecisionRequest(
            request_type="correction",
            data={
                "message_id": "msg123",
                "correction": "修正后的内容",
                "original_message_id": "msg456",
            },
            task=None,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "update_message"

    @pytest.mark.asyncio
    async def test_handle_general_correction(self, handler):
        """测试处理一般修正"""
        request = DecisionRequest(
            request_type="correction",
            data={
                "message_id": "msg123",
                "correction": "一般修正内容",
                "context": {"key": "value"},
            },
            task=None,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "create_correction_task"

    def test_correction_request_validation(self):
        """测试修正请求验证"""
        with pytest.raises(ValidationError):
            CorrectionRequest()

        valid_request = CorrectionRequest(message_id="msg123", correction="测试修正")
        assert valid_request.message_id == "msg123"
        assert valid_request.correction == "测试修正"
        assert valid_request.task_id is None

    def test_correction_request_with_task_and_context(self):
        """测试包含任务和上下文的修正请求"""
        context = {"user_id": "user456", "conversation_id": "conv789"}
        request = CorrectionRequest(
            message_id="msg123",
            correction="带上下文的修正",
            task_id="task123",
            original_message_id="msg456",
            context=context,
        )
        assert request.task_id == "task123"
        assert request.original_message_id == "msg456"
        assert request.context == context

    @pytest.mark.asyncio
    async def test_analyze_correction_type(self, handler):
        """测试分析修正类型"""
        redo_correction = CorrectionRequest(message_id="msg123", correction="重新做")

        modify_correction = CorrectionRequest(
            message_id="msg124", correction="修改参数"
        )

        add_correction = CorrectionRequest(message_id="msg125", correction="补充内容")

        delete_correction = CorrectionRequest(message_id="msg126", correction="删除项")

        adjust_correction = CorrectionRequest(
            message_id="msg127", correction="调整设置"
        )

        general_correction = CorrectionRequest(
            message_id="msg128", correction="其他修正"
        )

        type1 = await handler._analyze_correction_type(redo_correction)
        type2 = await handler._analyze_correction_type(modify_correction)
        type3 = await handler._analyze_correction_type(add_correction)
        type4 = await handler._analyze_correction_type(delete_correction)
        type5 = await handler._analyze_correction_type(adjust_correction)
        type6 = await handler._analyze_correction_type(general_correction)

        assert type1 == "redo"
        assert type2 == "modify"
        assert type3 == "add"
        assert type4 == "delete"
        assert type5 == "adjust"
        assert type6 == "general"
