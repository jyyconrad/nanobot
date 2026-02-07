"""
MainAgent 会话 Hooks - 用于扩展 MainAgent 功能
"""

import logging
from typing import Any, Dict, Optional

from pydantic import BaseModel

from nanobot.agent.decision.models import DecisionResult
from nanobot.agent.planner.models import TaskPlan
from nanobot.agent.subagent.models import SubagentResult, SubagentTask

logger = logging.getLogger(__name__)


class HookResult(BaseModel):
    """Hook 结果模型"""

    allow: bool = True
    block: bool = False
    modified_message: Optional[str] = None


class MainAgentHooks:
    """
    MainAgent 会话 Hooks

    提供在 MainAgent 处理消息过程中的各个阶段的扩展点
    """

    async def on_message_receive(self, message: str, session_id: str) -> HookResult:
        """
        当收到新消息时触发

        Args:
            message: 用户输入的消息
            session_id: 会话 ID

        Returns:
            Hook 处理结果
        """
        logger.debug(f"MainAgentHooks.on_message_receive: session={session_id}, message={message}")
        return HookResult()

    async def before_planning(self, message: str) -> HookResult:
        """
        在任务规划之前触发

        Args:
            message: 用户输入的消息

        Returns:
            Hook 处理结果
        """
        logger.debug(f"MainAgentHooks.before_planning: message={message}")
        return HookResult()

    async def after_planning(self, result: TaskPlan) -> None:
        """
        在任务规划之后触发

        Args:
            result: 任务规划结果
        """
        logger.debug(f"MainAgentHooks.after_planning: {result}")

    async def before_decision(self, trigger: str) -> HookResult:
        """
        在执行决策之前触发

        Args:
            trigger: 决策触发器

        Returns:
            Hook 处理结果
        """
        logger.debug(f"MainAgentHooks.before_decision: trigger={trigger}")
        return HookResult()

    async def after_decision(self, decision: DecisionResult) -> None:
        """
        在执行决策之后触发

        Args:
            decision: 执行决策结果
        """
        logger.debug(f"MainAgentHooks.after_decision: {decision}")

    async def on_subagent_spawn(self, agent_id: str, task: SubagentTask) -> None:
        """
        当生成 Subagent 时触发

        Args:
            agent_id: Subagent 实例 ID
            task: Subagent 任务描述
        """
        logger.debug(f"MainAgentHooks.on_subagent_spawn: agent={agent_id}, task={task}")

    async def on_subagent_result(self, result: SubagentResult) -> None:
        """
        当收到 Subagent 结果时触发

        Args:
            result: Subagent 执行结果
        """
        logger.debug(f"MainAgentHooks.on_subagent_result: {result}")

    async def on_subagent_interrupt(self, message: str) -> None:
        """
        当 Subagent 被中断时触发

        Args:
            message: 中断消息
        """
        logger.debug(f"MainAgentHooks.on_subagent_interrupt: {message}")

    async def on_task_cancelled(self, task: str) -> None:
        """
        当任务被取消时触发

        Args:
            task: 被取消的任务描述
        """
        logger.debug(f"MainAgentHooks.on_task_cancelled: {task}")

    async def on_response_send(self, response: str, session_id: str) -> None:
        """
        当发送响应给用户时触发

        Args:
            response: 要发送的响应
            session_id: 会话 ID
        """
        logger.debug(f"MainAgentHooks.on_response_send: session={session_id}, response={response}")

    async def on_error(self, error: Exception, session_id: str) -> Optional[str]:
        """
        当处理过程中发生错误时触发

        Args:
            error: 错误信息
            session_id: 会话 ID

        Returns:
            可选的错误响应，用于替换默认响应
        """
        logger.error(f"MainAgentHooks.on_error: session={session_id}, error={error}")
        return None


class MainAgentHooksDecorator(MainAgentHooks):
    """
    MainAgent Hooks 装饰器基类

    用于方便地创建自定义 Hooks 装饰器
    """

    def __init__(self, base: MainAgentHooks = None):
        self.base = base or MainAgentHooks()

    async def on_message_receive(self, message: str, session_id: str) -> HookResult:
        return await self.base.on_message_receive(message, session_id)

    async def before_planning(self, message: str) -> HookResult:
        return await self.base.before_planning(message)

    async def after_planning(self, result: TaskPlan) -> None:
        await self.base.after_planning(result)

    async def before_decision(self, trigger: str) -> HookResult:
        return await self.base.before_decision(trigger)

    async def after_decision(self, decision: DecisionResult) -> None:
        await self.base.after_decision(decision)

    async def on_subagent_spawn(self, agent_id: str, task: SubagentTask) -> None:
        await self.base.on_subagent_spawn(agent_id, task)

    async def on_subagent_result(self, result: SubagentResult) -> None:
        await self.base.on_subagent_result(result)

    async def on_subagent_interrupt(self, message: str) -> None:
        await self.base.on_subagent_interrupt(message)

    async def on_task_cancelled(self, task: str) -> None:
        await self.base.on_task_cancelled(task)

    async def on_response_send(self, response: str, session_id: str) -> None:
        await self.base.on_response_send(response, session_id)

    async def on_error(self, error: Exception, session_id: str) -> Optional[str]:
        return await self.base.on_error(error, session_id)


class LoggingHooksDecorator(MainAgentHooksDecorator):
    """
    日志记录 Hooks 装饰器

    用于记录 MainAgent 的所有阶段
    """

    async def on_message_receive(self, message: str, session_id: str) -> HookResult:
        logger.info(f"Received message: session={session_id}, message='{message}'")
        return await super().on_message_receive(message, session_id)

    async def before_planning(self, message: str) -> HookResult:
        logger.info(f"Before planning: message='{message}'")
        return await super().before_planning(message)

    async def after_planning(self, result: TaskPlan) -> None:
        logger.info(f"After planning: {result}")
        await super().after_planning(result)

    async def before_decision(self, trigger: str) -> HookResult:
        logger.info(f"Before decision: trigger={trigger}")
        return await super().before_decision(trigger)

    async def after_decision(self, decision: DecisionResult) -> None:
        logger.info(f"After decision: {decision}")
        await super().after_decision(decision)

    async def on_subagent_spawn(self, agent_id: str, task: SubagentTask) -> None:
        logger.info(f"Subagent spawned: agent={agent_id}, task='{task.description}'")
        await super().on_subagent_spawn(agent_id, task)

    async def on_subagent_result(self, result: SubagentResult) -> None:
        logger.info(f"Subagent result: {result}")
        await super().on_subagent_result(result)

    async def on_subagent_interrupt(self, message: str) -> None:
        logger.info(f"Subagent interrupted: message='{message}'")
        await super().on_subagent_interrupt(message)

    async def on_task_cancelled(self, task: str) -> None:
        logger.info(f"Task cancelled: '{task}'")
        await super().on_task_cancelled(task)

    async def on_response_send(self, response: str, session_id: str) -> None:
        logger.info(f"Response sent: session={session_id}, response='{response}'")
        await super().on_response_send(response, session_id)

    async def on_error(self, error: Exception, session_id: str) -> Optional[str]:
        logger.error(f"Error: session={session_id}, error={error}", exc_info=True)
        return await super().on_error(error, session_id)


class MetricsHooksDecorator(MainAgentHooksDecorator):
    """
    指标收集 Hooks 装饰器

    用于收集 MainAgent 的性能指标
    """

    def __init__(self, base: MainAgentHooks = None):
        super().__init__(base)
        self.metrics: Dict[str, Any] = {}

    async def on_message_receive(self, message: str, session_id: str) -> HookResult:
        self.metrics["message_receive_count"] = self.metrics.get("message_receive_count", 0) + 1
        self.metrics["last_message_time"] = message  # 实际应该是时间戳
        return await super().on_message_receive(message, session_id)

    async def after_planning(self, result: TaskPlan) -> None:
        self.metrics["planning_count"] = self.metrics.get("planning_count", 0) + 1
        if hasattr(result, "task_type"):
            self.metrics["last_planning_action"] = result.task_type
        await super().after_planning(result)

    async def after_decision(self, decision: DecisionResult) -> None:
        self.metrics["decision_count"] = self.metrics.get("decision_count", 0) + 1
        self.metrics["last_decision_action"] = decision.action
        await super().after_decision(decision)

    async def on_subagent_spawn(self, agent_id: str, task: SubagentTask) -> None:
        self.metrics["subagent_spawn_count"] = self.metrics.get("subagent_spawn_count", 0) + 1
        await super().on_subagent_spawn(agent_id, task)

    async def on_subagent_result(self, result: SubagentResult) -> None:
        self.metrics["subagent_result_count"] = self.metrics.get("subagent_result_count", 0) + 1
        self.metrics["last_subagent_status"] = result.state.status
        await super().on_subagent_result(result)

    def get_metrics(self) -> Dict[str, Any]:
        """获取收集到的指标"""
        return self.metrics
