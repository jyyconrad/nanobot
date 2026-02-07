"""
MainAgentHooks 单元测试
"""


import pytest

from nanobot.agent.decision.models import DecisionResult
from nanobot.agent.hooks import (
    HookResult,
    LoggingHooksDecorator,
    MainAgentHooks,
    MetricsHooksDecorator,
)
from nanobot.agent.planner.models import TaskPlan
from nanobot.agent.subagent.models import (
    SubagentResult,
    SubagentState,
    SubagentStatus,
    SubagentTask,
)


@pytest.fixture
def base_hooks():
    """创建基础 Hooks 实例"""
    return MainAgentHooks()


@pytest.mark.asyncio
async def test_base_hooks_on_message_receive(base_hooks):
    """测试基础 Hooks 的 on_message_receive 方法"""
    result = await base_hooks.on_message_receive("test message", "test-session")
    assert isinstance(result, HookResult)
    assert result.allow is True
    assert result.block is False
    assert result.modified_message is None


@pytest.mark.asyncio
async def test_base_hooks_before_planning(base_hooks):
    """测试基础 Hooks 的 before_planning 方法"""
    result = await base_hooks.before_planning("test message")
    assert isinstance(result, HookResult)
    assert result.allow is True
    assert result.block is False
    assert result.modified_message is None


@pytest.mark.asyncio
async def test_base_hooks_after_planning(base_hooks):
    """测试基础 Hooks 的 after_planning 方法"""
    from nanobot.agent.planner.models import TaskPriority, TaskType

    task_plan = TaskPlan(
        task_type=TaskType.OTHER,
        priority=TaskPriority.MEDIUM,
        complexity=0.5,
        steps=["step1", "step2"],
        estimated_time=300,
        requires_approval=False,
    )
    await base_hooks.after_planning(task_plan)


@pytest.mark.asyncio
async def test_base_hooks_before_decision(base_hooks):
    """测试基础 Hooks 的 before_decision 方法"""
    result = await base_hooks.before_decision("new_message")
    assert isinstance(result, HookResult)
    assert result.allow is True
    assert result.block is False
    assert result.modified_message is None


@pytest.mark.asyncio
async def test_base_hooks_after_decision(base_hooks):
    """测试基础 Hooks 的 after_decision 方法"""
    decision = DecisionResult(success=True, action="reply", data={}, message="test response")
    await base_hooks.after_decision(decision)


@pytest.mark.asyncio
async def test_base_hooks_on_subagent_spawn(base_hooks):
    """测试基础 Hooks 的 on_subagent_spawn 方法"""
    task = SubagentTask(task_id="test-task", description="test task")
    await base_hooks.on_subagent_spawn("test-agent", task)


@pytest.mark.asyncio
async def test_base_hooks_on_subagent_result(base_hooks):
    """测试基础 Hooks 的 on_subagent_result 方法"""
    result = SubagentResult(
        task_id="test-task",
        output="test output",
        success=True,
        state=SubagentState(task_id="test-task", status=SubagentStatus.COMPLETED, progress=1.0),
    )
    await base_hooks.on_subagent_result(result)


@pytest.mark.asyncio
async def test_base_hooks_on_subagent_interrupt(base_hooks):
    """测试基础 Hooks 的 on_subagent_interrupt 方法"""
    await base_hooks.on_subagent_interrupt("interrupt message")


@pytest.mark.asyncio
async def test_base_hooks_on_task_cancelled(base_hooks):
    """测试基础 Hooks 的 on_task_cancelled 方法"""
    await base_hooks.on_task_cancelled("test task")


@pytest.mark.asyncio
async def test_base_hooks_on_response_send(base_hooks):
    """测试基础 Hooks 的 on_response_send 方法"""
    await base_hooks.on_response_send("test response", "test-session")


@pytest.mark.asyncio
async def test_base_hooks_on_error(base_hooks):
    """测试基础 Hooks 的 on_error 方法"""
    error = Exception("Test error")
    result = await base_hooks.on_error(error, "test-session")
    assert result is None


@pytest.mark.asyncio
async def test_logging_hooks_decorator():
    """测试 LoggingHooksDecorator"""
    base_hooks = MainAgentHooks()
    logging_hooks = LoggingHooksDecorator(base_hooks)

    # 测试所有方法都能正常调用
    await logging_hooks.on_message_receive("test message", "test-session")
    await logging_hooks.before_planning("test message")
    from nanobot.agent.planner.models import TaskPriority, TaskType

    task_plan = TaskPlan(
        task_type=TaskType.OTHER,
        priority=TaskPriority.MEDIUM,
        complexity=0.5,
        steps=["step1", "step2"],
        estimated_time=300,
        requires_approval=False,
    )
    await logging_hooks.after_planning(task_plan)
    await logging_hooks.before_decision("new_message")
    decision = DecisionResult(success=True, action="reply", data={}, message="test response")
    await logging_hooks.after_decision(decision)
    task = SubagentTask(task_id="test-task", description="test task")
    await logging_hooks.on_subagent_spawn("test-agent", task)
    result = SubagentResult(
        task_id="test-task",
        output="test output",
        success=True,
        state=SubagentState(task_id="test-task", status=SubagentStatus.COMPLETED, progress=1.0),
    )
    await logging_hooks.on_subagent_result(result)
    await logging_hooks.on_subagent_interrupt("interrupt message")
    await logging_hooks.on_task_cancelled("test task")
    await logging_hooks.on_response_send("test response", "test-session")
    await logging_hooks.on_error(Exception("Test error"), "test-session")


@pytest.mark.asyncio
async def test_metrics_hooks_decorator():
    """测试 MetricsHooksDecorator"""
    base_hooks = MainAgentHooks()
    metrics_hooks = MetricsHooksDecorator(base_hooks)

    # 测试指标收集
    await metrics_hooks.on_message_receive("test message", "test-session")
    await metrics_hooks.on_message_receive("another message", "test-session")

    from nanobot.agent.planner.models import TaskPriority, TaskType

    task_plan = TaskPlan(
        task_type=TaskType.OTHER,
        priority=TaskPriority.MEDIUM,
        complexity=0.5,
        steps=["step1", "step2"],
        estimated_time=300,
        requires_approval=False,
    )
    await metrics_hooks.after_planning(task_plan)

    decision = DecisionResult(success=True, action="reply", data={}, message="test response")
    await metrics_hooks.after_decision(decision)

    task = SubagentTask(task_id="test-task", description="test task")
    await metrics_hooks.on_subagent_spawn("test-agent", task)

    result = SubagentResult(
        task_id="test-task",
        output="test output",
        success=True,
        state=SubagentState(task_id="test-task", status=SubagentStatus.COMPLETED, progress=1.0),
    )
    await metrics_hooks.on_subagent_result(result)

    # 获取指标
    metrics = metrics_hooks.get_metrics()

    assert "message_receive_count" in metrics
    assert metrics["message_receive_count"] == 2
    assert "planning_count" in metrics
    assert metrics["planning_count"] == 1
    assert "decision_count" in metrics
    assert metrics["decision_count"] == 1
    assert "subagent_spawn_count" in metrics
    assert metrics["subagent_spawn_count"] == 1
    assert "subagent_result_count" in metrics
    assert metrics["subagent_result_count"] == 1
    assert "last_planning_action" in metrics
    assert metrics["last_planning_action"] == "other"
    assert "last_decision_action" in metrics
    assert metrics["last_decision_action"] == "reply"


@pytest.mark.asyncio
async def test_hook_result_creation():
    """测试 HookResult 创建"""
    # 默认值
    default_result = HookResult()
    assert default_result.allow is True
    assert default_result.block is False
    assert default_result.modified_message is None

    # 自定义值
    custom_result = HookResult(allow=False, block=True, modified_message="modified message")
    assert custom_result.allow is False
    assert custom_result.block is True
    assert custom_result.modified_message == "modified message"


@pytest.mark.asyncio
async def test_hooks_decorator_chain():
    """测试 Hooks 装饰器链"""
    base_hooks = MainAgentHooks()
    logging_hooks = LoggingHooksDecorator(base_hooks)
    metrics_hooks = MetricsHooksDecorator(logging_hooks)

    await metrics_hooks.on_message_receive("test message", "test-session")

    metrics = metrics_hooks.get_metrics()
    assert "message_receive_count" in metrics
    assert metrics["message_receive_count"] == 1
