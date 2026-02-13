"""
MainAgent 单元测试
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from nanobot.agent.decision.models import DecisionResult
from nanobot.agent.main_agent import MainAgent, MainAgentState
from nanobot.agent.planner.models import TaskPlan, TaskPriority, TaskStep, TaskType
from nanobot.agent.subagent.models import SubagentState, SubagentStatus, SubagentTask


@pytest.fixture
def mock_context_manager():
    """创建模拟的 ContextManager"""
    mock = Mock()
    mock.build_context = AsyncMock(return_value=("mock context", None))
    return mock


@pytest.fixture
def mock_task_planner():
    """创建模拟的 TaskPlanner"""
    mock = Mock()

    mock.plan_task = AsyncMock(
        return_value=TaskPlan(
            task_type=TaskType.CODE_GENERATION,
            priority=TaskPriority.MEDIUM,
            complexity=0.7,
            steps=[
                TaskStep(
                    id="step1",
                    description="step1",
                    expected_output="output1",
                    validation_criteria="valid1",
                ),
                TaskStep(
                    id="step2",
                    description="step2",
                    expected_output="output2",
                    validation_criteria="valid2",
                ),
            ],
            estimated_time=600,
            requires_approval=True,
        )
    )
    mock.cancellation_detector = Mock()
    mock.cancellation_detector.is_cancellation = AsyncMock(return_value=False)
    mock.correction_detector = Mock()
    mock.correction_detector.detect_correction = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_decision_maker():
    """创建模拟的 ExecutionDecisionMaker"""
    mock = Mock()
    mock.make_decision = AsyncMock(
        return_value=DecisionResult(
            success=True, action="reply", data={}, message="Test response"
        )
    )
    return mock


@pytest.fixture
def mock_subagent_manager():
    """创建模拟的 SubagentManager"""
    mock = Mock()
    mock.spawn_subagent = AsyncMock(return_value="test-agent-id")
    mock.cancel_subagent = AsyncMock()
    mock.interrupt_subagent = AsyncMock()
    return mock


@pytest.fixture
def mock_hooks():
    """创建模拟的 MainAgentHooks"""
    from nanobot.agent.hooks import MainAgentHooks

    mock = Mock(spec=MainAgentHooks)
    for attr in dir(MainAgentHooks):
        if not attr.startswith("__") and callable(getattr(MainAgentHooks, attr)):
            setattr(mock, attr, AsyncMock())
    return mock


@pytest.mark.asyncio
async def test_main_agent_initialization():
    """测试 MainAgent 初始化"""
    session_id = "test-session"
    agent = MainAgent(session_id)

    assert isinstance(agent, MainAgent)
    assert agent.session_id == session_id
    assert isinstance(agent.state, MainAgentState)
    assert agent.state.session_id == session_id
    assert not agent.state.is_processing
    assert agent.state.current_task is None
    assert len(agent.state.subagent_tasks) == 0


@pytest.mark.asyncio
@patch("nanobot.agent.main_agent.ContextManager")
@patch("nanobot.agent.main_agent.TaskPlanner")
@patch("nanobot.agent.main_agent.ExecutionDecisionMaker")
@patch("nanobot.agent.main_agent.SubagentManager")
@patch("nanobot.agent.main_agent.MainAgentHooks")
async def test_process_message_new_task(
    mock_hooks_cls, mock_sa_manager_cls, mock_dm_cls, mock_tp_cls, mock_cm_cls
):
    """测试处理新任务消息"""
    # 设置 mock
    mock_cm = Mock()
    mock_cm.build_context = AsyncMock(return_value=("mock context", None))
    mock_cm.get_history = Mock(return_value=[])
    mock_cm_cls.return_value = mock_cm

    mock_tp = Mock()

    mock_tp.plan_task = AsyncMock(
        return_value=TaskPlan(
            task_type=TaskType.CODE_GENERATION,
            priority=TaskPriority.MEDIUM,
            complexity=0.7,
            steps=[
                TaskStep(
                    id="step1",
                    description="step1",
                    expected_output="output1",
                    validation_criteria="valid1",
                ),
                TaskStep(
                    id="step2",
                    description="step2",
                    expected_output="output2",
                    validation_criteria="valid2",
                ),
            ],
            estimated_time=600,
            requires_approval=True,
        )
    )
    mock_tp.cancellation_detector = Mock()
    mock_tp.cancellation_detector.is_cancellation = AsyncMock(return_value=False)
    mock_tp.correction_detector = Mock()
    mock_tp.correction_detector.detect_correction = AsyncMock(return_value=None)
    mock_tp_cls.return_value = mock_tp

    mock_dm = Mock()
    mock_dm.make_decision = AsyncMock(
        return_value=DecisionResult(
            success=True, action="reply", data={}, message="Task completed"
        )
    )
    mock_dm_cls.return_value = mock_dm

    mock_sa = Mock()
    mock_sa_manager_cls.return_value = mock_sa

    mock_hooks = Mock()
    for attr in [
        "on_message_receive",
        "before_planning",
        "after_planning",
        "before_decision",
        "after_decision",
        "on_response_send",
    ]:
        setattr(mock_hooks, attr, AsyncMock())
    setattr(
        mock_hooks,
        "on_message_receive",
        AsyncMock(return_value=Mock(allow=True, block=False, modified_message=None)),
    )
    setattr(
        mock_hooks,
        "before_planning",
        AsyncMock(return_value=Mock(allow=True, block=False, modified_message=None)),
    )
    setattr(
        mock_hooks,
        "before_decision",
        AsyncMock(return_value=Mock(allow=True, block=False, modified_message=None)),
    )
    mock_hooks_cls.return_value = mock_hooks

    # 模拟 LLM 响应
    with patch(
        "nanobot.providers.litellm_provider.LiteLLMProvider"
    ) as mock_provider_cls:
        mock_provider = Mock()
        mock_response = Mock()
        mock_response.content = "Task completed"
        mock_response.has_tool_calls = False
        mock_provider.chat = AsyncMock(return_value=mock_response)
        mock_provider_cls.return_value = mock_provider

        # 测试
        agent = MainAgent("test-session")
        response = await agent.process_message("Test message")

    assert isinstance(response, str)
    assert "Task completed" in response


@pytest.mark.asyncio
@patch("nanobot.agent.main_agent.ContextManager")
@patch("nanobot.agent.main_agent.TaskPlanner")
@patch("nanobot.agent.main_agent.ExecutionDecisionMaker")
@patch("nanobot.agent.main_agent.SubagentManager")
@patch("nanobot.agent.main_agent.MainAgentHooks")
async def test_process_message_with_error(
    mock_hooks_cls, mock_sa_manager_cls, mock_dm_cls, mock_tp_cls, mock_cm_cls
):
    """测试处理消息时发生错误"""
    # 设置 mock
    mock_cm = Mock()
    mock_cm.build_context = AsyncMock(side_effect=Exception("Context error"))
    mock_cm_cls.return_value = mock_cm

    mock_tp = Mock()
    mock_tp_cls.return_value = mock_tp

    mock_dm = Mock()
    mock_dm_cls.return_value = mock_dm

    mock_sa = Mock()
    mock_sa_manager_cls.return_value = mock_sa

    mock_hooks = Mock()
    for attr in [
        "on_message_receive",
        "before_planning",
        "after_planning",
        "before_decision",
        "after_decision",
        "on_response_send",
    ]:
        setattr(mock_hooks, attr, AsyncMock())
    setattr(
        mock_hooks,
        "on_message_receive",
        AsyncMock(return_value=Mock(allow=True, block=False, modified_message=None)),
    )
    setattr(
        mock_hooks,
        "before_planning",
        AsyncMock(return_value=Mock(allow=True, block=False, modified_message=None)),
    )
    setattr(
        mock_hooks,
        "before_decision",
        AsyncMock(return_value=Mock(allow=True, block=False, modified_message=None)),
    )
    mock_hooks_cls.return_value = mock_hooks

    # 测试
    agent = MainAgent("test-session")
    response = await agent.process_message("Test message")

    assert isinstance(response, str)
    assert "Context error" in response


@pytest.mark.asyncio
@patch("nanobot.agent.main_agent.ContextManager")
@patch("nanobot.agent.main_agent.TaskPlanner")
@patch("nanobot.agent.main_agent.ExecutionDecisionMaker")
@patch("nanobot.agent.main_agent.SubagentManager")
@patch("nanobot.agent.main_agent.MainAgentHooks")
async def test_process_message_cancellation(
    mock_hooks_cls, mock_sa_manager_cls, mock_dm_cls, mock_tp_cls, mock_cm_cls
):
    """测试处理任务取消消息"""
    # 设置 mock
    mock_cm = Mock()
    mock_cm.build_context = AsyncMock(return_value=("mock context", None))
    mock_cm.get_history = Mock(return_value=[])
    mock_cm_cls.return_value = mock_cm

    mock_tp = Mock()
    mock_tp.cancellation_detector = Mock()
    mock_tp.cancellation_detector.is_cancellation = AsyncMock(return_value=True)
    mock_tp_cls.return_value = mock_tp

    mock_dm = Mock()
    mock_dm_cls.return_value = mock_dm

    mock_sa = Mock()
    mock_sa.cancel_subagent = AsyncMock()
    mock_sa_manager_cls.return_value = mock_sa

    mock_hooks = Mock()
    for attr in ["on_message_receive", "on_task_cancelled"]:
        setattr(mock_hooks, attr, AsyncMock())
    setattr(
        mock_hooks,
        "on_message_receive",
        AsyncMock(return_value=Mock(allow=True, block=False, modified_message=None)),
    )
    setattr(
        mock_hooks,
        "before_planning",
        AsyncMock(return_value=Mock(allow=True, block=False, modified_message=None)),
    )
    setattr(
        mock_hooks,
        "before_decision",
        AsyncMock(return_value=Mock(allow=True, block=False, modified_message=None)),
    )
    mock_hooks_cls.return_value = mock_hooks

    # 测试
    agent = MainAgent("test-session")
    agent.state.current_task = "current task"
    response = await agent.process_message("取消任务")

    assert isinstance(response, str)
    assert "已取消" in response


@pytest.mark.asyncio
@patch("nanobot.agent.main_agent.ContextManager")
@patch("nanobot.agent.main_agent.TaskPlanner")
@patch("nanobot.agent.main_agent.ExecutionDecisionMaker")
@patch("nanobot.agent.main_agent.SubagentManager")
@patch("nanobot.agent.main_agent.MainAgentHooks")
async def test_process_message_correction(
    mock_hooks_cls, mock_sa_manager_cls, mock_dm_cls, mock_tp_cls, mock_cm_cls
):
    """测试处理任务修正消息"""
    # 设置 mock
    mock_cm = Mock()
    mock_cm.build_context = AsyncMock(return_value=("mock context", None))
    mock_cm.get_history = Mock(return_value=[])
    mock_cm_cls.return_value = mock_cm

    mock_tp = Mock()
    mock_tp.cancellation_detector = Mock()
    mock_tp.cancellation_detector.is_cancellation = AsyncMock(return_value=False)
    mock_tp.correction_detector = Mock()
    mock_tp.correction_detector.detect_correction = AsyncMock(return_value=True)

    mock_tp.plan_task = AsyncMock(
        return_value=TaskPlan(
            task_type=TaskType.CODE_GENERATION,
            priority=TaskPriority.MEDIUM,
            complexity=0.5,
            steps=[
                TaskStep(
                    id="step1",
                    description="step1",
                    expected_output="output1",
                    validation_criteria="valid1",
                )
            ],
            estimated_time=300,
            requires_approval=False,
        )
    )
    mock_tp_cls.return_value = mock_tp

    mock_dm = Mock()
    mock_dm.make_decision = AsyncMock(
        return_value=DecisionResult(
            success=True, action="reply", data={}, message="Corrected task completed"
        )
    )
    mock_dm_cls.return_value = mock_dm

    mock_sa = Mock()
    mock_sa.cancel_subagent = AsyncMock()
    mock_sa_manager_cls.return_value = mock_sa

    mock_hooks = Mock()
    for attr in [
        "on_message_receive",
        "before_planning",
        "after_planning",
        "before_decision",
        "after_decision",
        "on_response_send",
    ]:
        setattr(mock_hooks, attr, AsyncMock())
    setattr(
        mock_hooks,
        "on_message_receive",
        AsyncMock(return_value=Mock(allow=True, block=False, modified_message=None)),
    )
    setattr(
        mock_hooks,
        "before_planning",
        AsyncMock(return_value=Mock(allow=True, block=False, modified_message=None)),
    )
    setattr(
        mock_hooks,
        "before_decision",
        AsyncMock(return_value=Mock(allow=True, block=False, modified_message=None)),
    )
    mock_hooks_cls.return_value = mock_hooks

    # 模拟 LLM 响应
    with patch(
        "nanobot.providers.litellm_provider.LiteLLMProvider"
    ) as mock_provider_cls:
        mock_provider = Mock()
        mock_response = Mock()
        mock_response.content = "Corrected task completed"
        mock_response.has_tool_calls = False
        mock_provider.chat = AsyncMock(return_value=mock_response)
        mock_provider_cls.return_value = mock_provider

        # 测试
        agent = MainAgent("test-session")
        agent.state.current_task = "current task"
        response = await agent.process_message("修正任务：新要求")

    assert isinstance(response, str)
    assert "Corrected task completed" in response


@pytest.mark.asyncio
async def test_main_agent_get_status():
    """测试获取 MainAgent 状态"""
    agent = MainAgent("test-session")
    agent.state.current_task = "test task"
    agent.state.subagent_tasks["test-agent"] = SubagentTask(
        task_id="test-agent", description="subtask"
    )
    agent.state.subagent_states["test-agent"] = SubagentState(
        task_id="test-agent", status=SubagentStatus.RUNNING, progress=0.5
    )

    status = await agent.get_status()

    assert status["session_id"] == "test-session"
    assert status["current_task"] == "test task"
    assert status["subagent_count"] == 1
    assert status["running_count"] == 1
