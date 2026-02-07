"""
测试子代理结果处理程序
"""

from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from nanobot.agent.decision.models import DecisionRequest, DecisionResult, SubagentResultRequest
from nanobot.agent.decision.subagent_result_handler import SubagentResultHandler
from nanobot.agent.loop import AgentLoop
from nanobot.agent.task import Task


class TestSubagentResultHandler:
    """测试 SubagentResultHandler 类"""

    @pytest.fixture
    def mock_agent_loop(self):
        """创建模拟的 AgentLoop"""
        mock = Mock(spec=AgentLoop)
        return mock

    @pytest.fixture
    def handler(self, mock_agent_loop):
        """创建子代理结果处理程序实例"""
        return SubagentResultHandler(mock_agent_loop)

    @pytest.fixture
    def mock_task(self):
        """创建模拟的任务"""
        mock_task = Mock(spec=Task)
        mock_task.id = "task123"
        mock_task.status = "running"
        mock_task.retry_count = 0
        mock_task.max_retries = 3
        mock_task.next_step = None
        return mock_task

    @pytest.mark.asyncio
    async def test_initialization(self, handler, mock_agent_loop):
        """测试初始化"""
        assert handler is not None
        assert handler.agent_loop == mock_agent_loop

    @pytest.mark.asyncio
    async def test_handle_request_valid_result(self, handler, mock_task):
        """测试处理有效结果请求"""
        request = DecisionRequest(
            request_type="subagent_result",
            data={
                "subagent_id": "sub123",
                "task_id": "task123",
                "result": {"success": True, "data": "test data"},
                "status": "success",
                "duration": 1.5,
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
            request_type="subagent_result",
            data={},  # 缺少必填字段
        )

        result = await handler.handle_request(request)
        assert not result.success
        assert result.action == "error"

    @pytest.mark.asyncio
    async def test_handle_success_result_no_next_step(self, handler, mock_task):
        """测试处理成功结果（无下一步）"""
        mock_task.next_step = None

        request = DecisionRequest(
            request_type="subagent_result",
            data={
                "subagent_id": "sub123",
                "task_id": "task123",
                "result": {"success": True, "data": "test data"},
                "status": "success",
                "duration": 1.5,
            },
            task=mock_task,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "complete_task"
        assert "result" in result.data

    @pytest.mark.asyncio
    async def test_handle_success_result_with_next_step(self, handler, mock_task):
        """测试处理成功结果（有下一步）"""
        mock_task.next_step = "step2"

        request = DecisionRequest(
            request_type="subagent_result",
            data={
                "subagent_id": "sub123",
                "task_id": "task123",
                "result": {"success": True, "data": "test data"},
                "status": "success",
                "duration": 1.5,
            },
            task=mock_task,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "continue_task"
        assert result.data["next_step"] == "step2"

    @pytest.mark.asyncio
    async def test_handle_error_result_retry_available(self, handler, mock_task):
        """测试处理错误结果（可以重试）"""
        mock_task.retry_count = 1
        mock_task.max_retries = 3

        request = DecisionRequest(
            request_type="subagent_result",
            data={
                "subagent_id": "sub123",
                "task_id": "task123",
                "result": {},
                "status": "error",
                "error": "Test error",
                "duration": 0.5,
            },
            task=mock_task,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "retry_task"
        assert "error" in result.data

    @pytest.mark.asyncio
    async def test_handle_error_result_no_retry(self, handler, mock_task):
        """测试处理错误结果（不可以重试）"""
        mock_task.retry_count = 3
        mock_task.max_retries = 3

        request = DecisionRequest(
            request_type="subagent_result",
            data={
                "subagent_id": "sub123",
                "task_id": "task123",
                "result": {},
                "status": "error",
                "error": "Test error",
                "duration": 0.5,
            },
            task=mock_task,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "fail_task"

    @pytest.mark.asyncio
    async def test_handle_cancelled_result(self, handler, mock_task):
        """测试处理取消结果"""
        request = DecisionRequest(
            request_type="subagent_result",
            data={
                "subagent_id": "sub123",
                "task_id": "task123",
                "result": {},
                "status": "cancelled",
                "duration": 0.2,
            },
            task=mock_task,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "cancel_task"

    @pytest.mark.asyncio
    async def test_handle_unknown_status(self, handler, mock_task):
        """测试处理未知状态"""
        request = DecisionRequest(
            request_type="subagent_result",
            data={
                "subagent_id": "sub123",
                "task_id": "task123",
                "result": {},
                "status": "unknown",
                "duration": 0.1,
            },
            task=mock_task,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "unknown_status"

    @pytest.mark.asyncio
    async def test_handle_no_task(self, handler):
        """测试处理无任务的结果"""
        request = DecisionRequest(
            request_type="subagent_result",
            data={
                "subagent_id": "sub123",
                "task_id": "task123",
                "result": {"success": True, "data": "test data"},
                "status": "success",
                "duration": 1.5,
            },
            task=None,
        )

        result = await handler.handle_request(request)
        assert result.success
        assert result.action == "task_not_found"

    def test_subagent_result_request_validation(self):
        """测试子代理结果请求验证"""
        with pytest.raises(ValidationError):
            SubagentResultRequest()

        valid_request = SubagentResultRequest(
            subagent_id="sub123",
            task_id="task123",
            result={"success": True},
            status="success",
            duration=1.5,
        )
        assert valid_request.subagent_id == "sub123"
        assert valid_request.task_id == "task123"
        assert valid_request.status == "success"
        assert valid_request.duration == 1.5

    def test_subagent_result_request_with_error(self):
        """测试包含错误信息的子代理结果请求"""
        request = SubagentResultRequest(
            subagent_id="sub123",
            task_id="task123",
            result={},
            status="error",
            duration=0.5,
            error="Test error message",
        )
        assert request.status == "error"
        assert request.error == "Test error message"
