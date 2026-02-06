"""
测试执行决策管理器
"""

import pytest
from unittest.mock import Mock, AsyncMock
from pydantic import ValidationError

from nanobot.agent.decision.decision_maker import ExecutionDecisionMaker
from nanobot.agent.decision.models import DecisionRequest, DecisionResult
from nanobot.agent.loop import AgentLoop


class TestExecutionDecisionMaker:
    """测试 ExecutionDecisionMaker 类"""

    @pytest.fixture
    def mock_agent_loop(self):
        """创建模拟的 AgentLoop"""
        mock = Mock(spec=AgentLoop)
        return mock

    @pytest.fixture
    def decision_maker(self, mock_agent_loop):
        """创建决策管理器实例"""
        return ExecutionDecisionMaker(mock_agent_loop)

    @pytest.mark.asyncio
    async def test_initialization(self, decision_maker, mock_agent_loop):
        """测试初始化"""
        assert decision_maker is not None
        assert decision_maker.agent_loop == mock_agent_loop
        assert "new_message" in decision_maker.list_supported_request_types()
        assert "subagent_result" in decision_maker.list_supported_request_types()
        assert "correction" in decision_maker.list_supported_request_types()
        assert "cancellation" in decision_maker.list_supported_request_types()

    @pytest.mark.asyncio
    async def test_make_decision_with_valid_request_type(self, decision_maker):
        """测试使用有效请求类型的决策"""
        # 模拟处理程序
        mock_handler = Mock()
        mock_handler.handle_request = AsyncMock(
            return_value=DecisionResult(success=True, action="test_action")
        )
        decision_maker.register_handler("test_type", mock_handler)

        request = DecisionRequest(
            request_type="test_type",
            data={"test": "data"}
        )

        result = await decision_maker.make_decision(request)
        assert result.success
        assert result.action == "test_action"
        mock_handler.handle_request.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_make_decision_with_unsupported_request_type(self, decision_maker):
        """测试使用不支持的请求类型的决策"""
        request = DecisionRequest(
            request_type="unsupported_type",
            data={"test": "data"}
        )

        result = await decision_maker.make_decision(request)
        assert not result.success
        assert result.action == "unknown"
        assert "不支持的请求类型" in result.message

    @pytest.mark.asyncio
    async def test_make_decision_with_handler_error(self, decision_maker):
        """测试处理程序错误"""
        # 模拟处理程序抛出异常
        mock_handler = Mock()
        mock_handler.handle_request = AsyncMock(
            side_effect=Exception("Test error")
        )
        decision_maker.register_handler("error_type", mock_handler)

        request = DecisionRequest(
            request_type="error_type",
            data={"test": "data"}
        )

        result = await decision_maker.make_decision(request)
        assert not result.success
        assert result.action == "error"
        assert "处理请求时发生错误" in result.message

    def test_register_and_get_handler(self, decision_maker):
        """测试注册和获取处理程序"""
        mock_handler = Mock()
        decision_maker.register_handler("custom_type", mock_handler)
        assert "custom_type" in decision_maker.list_supported_request_types()
        assert decision_maker.get_handler("custom_type") == mock_handler

    def test_list_supported_request_types(self, decision_maker):
        """测试获取支持的请求类型列表"""
        initial_types = decision_maker.list_supported_request_types()
        assert len(initial_types) >= 4  # 至少有四个默认处理程序

        new_handler = Mock()
        decision_maker.register_handler("new_type", new_handler)
        assert "new_type" in decision_maker.list_supported_request_types()
        assert len(decision_maker.list_supported_request_types()) == len(initial_types) + 1

    @pytest.mark.asyncio
    async def test_decision_request_validation(self):
        """测试决策请求验证"""
        with pytest.raises(ValidationError):
            DecisionRequest()

        valid_request = DecisionRequest(
            request_type="new_message",
            data={"content": "test message"}
        )
        assert valid_request.request_type == "new_message"
        assert valid_request.data == {"content": "test message"}


class TestDecisionResult:
    """测试 DecisionResult 类"""

    def test_decision_result_creation(self):
        """测试决策结果创建"""
        result = DecisionResult(success=True, action="test_action")
        assert result.success
        assert result.action == "test_action"
        assert result.data == {}
        assert result.message is None

    def test_decision_result_with_data_and_message(self):
        """测试包含数据和消息的决策结果"""
        data = {"key": "value"}
        message = "Test message"
        result = DecisionResult(
            success=True,
            action="test_action",
            data=data,
            message=message
        )
        assert result.data == data
        assert result.message == message

    def test_decision_result_failure(self):
        """测试失败的决策结果"""
        result = DecisionResult(success=False, action="error", message="Error message")
        assert not result.success
        assert result.action == "error"
        assert result.message == "Error message"
