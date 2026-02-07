"""
测试取消处理程序
"""

from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import ValidationError

from nanobot.agent.decision.cancellation_handler import CancellationHandler
from nanobot.agent.decision.models import CancellationRequest, DecisionRequest, DecisionResult
from nanobot.agent.loop import AgentLoop
from nanobot.agent.task import Task


class TestCancellationHandler:
    """测试 CancellationHandler 类"""

    @pytest.fixture
    def mock_agent_loop(self):
        """创建模拟的 AgentLoop"""
        mock = Mock(spec=AgentLoop)
        return mock

    @pytest.fixture
    def handler(self, mock_agent_loop):
        """创建取消处理程序实例"""
        return CancellationHandler(mock_agent_loop)

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
    async def test_handle_request_valid_cancellation(self, handler, mock_task):
        """测试处理有效取消请求"""
        request = DecisionRequest(
            request_type="cancellation",
            data={"message_id": "msg123", "cancellation_reason": "用户取消", "task_id": "task123"},
            task=mock_task,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert isinstance(result, DecisionResult)

    @pytest.mark.asyncio
    async def test_handle_request_invalid_data(self, handler):
        """测试处理无效数据请求"""
        request = DecisionRequest(
            request_type="cancellation",
            data={},  # 缺少必填字段
        )

        result = await handler.handle_request(request)
        assert not result.success
        assert result.action == "error"

    @pytest.mark.asyncio
    async def test_handle_task_cancellation_running(self, handler, mock_task):
        """测试处理正在运行的任务取消"""
        mock_task.status = "running"

        request = DecisionRequest(
            request_type="cancellation",
            data={
                "message_id": "msg123",
                "cancellation_reason": "任务不再需要",
                "task_id": "task123",
            },
            task=mock_task,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "cancel_task"

    @pytest.mark.asyncio
    async def test_handle_task_cancellation_completed(self, handler, mock_task):
        """测试处理已完成的任务取消"""
        mock_task.status = "completed"

        request = DecisionRequest(
            request_type="cancellation",
            data={
                "message_id": "msg123",
                "cancellation_reason": "任务已完成",
                "task_id": "task123",
            },
            task=mock_task,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "task_already_ended"

    @pytest.mark.asyncio
    async def test_handle_task_id_cancellation(self, handler, mock_agent_loop):
        """测试通过任务ID取消任务"""
        # 模拟任务管理器
        mock_task = Mock(spec=Task)
        mock_task.id = "task123"
        mock_task.status = "running"

        mock_task_manager = Mock()
        mock_task_manager.get_task = AsyncMock(return_value=mock_task)
        mock_agent_loop.task_manager = mock_task_manager

        request = DecisionRequest(
            request_type="cancellation",
            data={
                "message_id": "msg123",
                "cancellation_reason": "通过ID取消",
                "task_id": "task123",
            },
            task=None,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "cancel_task"

    @pytest.mark.asyncio
    async def test_handle_task_id_not_found(self, handler, mock_agent_loop):
        """测试任务ID不存在的情况"""
        mock_task_manager = Mock()
        mock_task_manager.get_task = AsyncMock(return_value=None)
        mock_agent_loop.task_manager = mock_task_manager

        request = DecisionRequest(
            request_type="cancellation",
            data={
                "message_id": "msg123",
                "cancellation_reason": "任务不存在",
                "task_id": "nonexistent_task",
            },
            task=None,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "task_not_found"

    @pytest.mark.asyncio
    async def test_handle_multiple_active_tasks(self, handler, mock_agent_loop):
        """测试处理多个正在运行的任务"""
        # 模拟任务管理器
        task1 = Mock(spec=Task)
        task1.id = "task123"
        task1.status = "running"

        task2 = Mock(spec=Task)
        task2.id = "task456"
        task2.status = "running"

        mock_task_manager = Mock()
        mock_task_manager.get_all_tasks = AsyncMock(return_value=[task1, task2])
        mock_agent_loop.task_manager = mock_task_manager

        request = DecisionRequest(
            request_type="cancellation",
            data={"message_id": "msg123", "cancellation_reason": "取消所有任务"},
            task=None,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "multiple_tasks_found"
        assert len(result.data["task_ids"]) == 2

    @pytest.mark.asyncio
    async def test_handle_no_active_tasks(self, handler, mock_agent_loop):
        """测试没有正在运行的任务"""
        mock_task_manager = Mock()
        mock_task_manager.get_all_tasks = AsyncMock(return_value=[])
        mock_agent_loop.task_manager = mock_task_manager

        request = DecisionRequest(
            request_type="cancellation",
            data={"message_id": "msg123", "cancellation_reason": "取消任务"},
            task=None,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "no_tasks_to_cancel"

    @pytest.mark.asyncio
    async def test_handle_single_active_task(self, handler, mock_agent_loop):
        """测试处理单个正在运行的任务"""
        mock_task = Mock(spec=Task)
        mock_task.id = "task123"
        mock_task.status = "running"

        mock_task_manager = Mock()
        mock_task_manager.get_all_tasks = AsyncMock(return_value=[mock_task])
        mock_agent_loop.task_manager = mock_task_manager

        request = DecisionRequest(
            request_type="cancellation",
            data={"message_id": "msg123", "cancellation_reason": "取消任务"},
            task=None,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "cancel_task"

    def test_cancellation_request_validation(self):
        """测试取消请求验证"""
        with pytest.raises(ValidationError):
            CancellationRequest()

        valid_request = CancellationRequest(message_id="msg123")
        assert valid_request.message_id == "msg123"
        assert valid_request.cancellation_reason is None

    def test_cancellation_request_with_reason_and_context(self):
        """测试包含原因和上下文的取消请求"""
        context = {"user_id": "user456", "conversation_id": "conv789"}
        request = CancellationRequest(
            message_id="msg123",
            cancellation_reason="用户主动取消",
            task_id="task123",
            context=context,
        )
        assert request.cancellation_reason == "用户主动取消"
        assert request.task_id == "task123"
        assert request.context == context

    @pytest.mark.asyncio
    async def test_validate_cancellation_request(self, handler):
        """测试验证取消请求"""
        valid_request = CancellationRequest(
            message_id="msg123", cancellation_reason="有效的取消原因"
        )

        invalid_request = CancellationRequest(message_id="msg123", cancellation_reason="短")

        result1 = await handler._validate_cancellation_request(valid_request)
        result2 = await handler._validate_cancellation_request(invalid_request)

        assert result1 is True
        assert result2 is False
