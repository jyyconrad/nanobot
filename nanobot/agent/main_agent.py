"""
MainAgent 主代理类 - 协调所有组件的核心入口
"""

import logging
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel

from nanobot.agent.context_manager import ContextManager, ContextStats
from nanobot.agent.decision.decision_maker import ExecutionDecisionMaker
from nanobot.agent.decision.models import DecisionRequest, DecisionResult
from nanobot.agent.hooks import MainAgentHooks
from nanobot.agent.planner.models import TaskPlan
from nanobot.agent.planner.task_planner import TaskPlanner
from nanobot.agent.subagent.manager import SubagentManager
from nanobot.agent.subagent.models import SubagentResult, SubagentState, SubagentTask
from nanobot.agent.workflow.message_router import MessageRouter
from nanobot.agent.workflow.models import MessageCategory
from nanobot.agent.workflow.workflow_manager import WorkflowManager

logger = logging.getLogger(__name__)


class MainAgentState(BaseModel):
    """MainAgent 状态模型"""

    session_id: str
    current_task: Optional[str] = None
    subagent_tasks: Dict[str, SubagentTask] = {}
    subagent_results: Dict[str, SubagentResult] = {}
    subagent_states: Dict[str, SubagentState] = {}
    context_stats: Optional[ContextStats] = None
    is_processing: bool = False


class MainAgent:
    """
    MainAgent 主代理类

    负责：
    - 用户消息接收和初步处理
    - 任务识别、规划和分解
    - 上下文和记忆管理
    - Subagent 调度和任务分配
    - Subagent 执行状态监控
    - 下一步动作决策
    - 用户响应聚合和总结
    """

    def __init__(self, session_id: str = None):
        if session_id is None:
            session_id = str(uuid4())  # 生成随机会话 ID
        self.session_id = session_id
        self.state = MainAgentState(session_id=session_id)
        self.context_manager = ContextManager()
        self.task_planner = TaskPlanner()
        # 注意：这里需要传递 agent_loop，但我们暂时设置为 None，因为我们还没有创建 loop
        self.decision_maker = ExecutionDecisionMaker(None)
        self.subagent_manager = SubagentManager()
        self.hooks = MainAgentHooks()
        # 新增：初始化消息路由器和工作流管理器
        self.message_router = MessageRouter()
        self.workflow_manager = WorkflowManager()

    async def process_message(self, message: str) -> str:
        """
        处理用户消息的主要入口

        Args:
            message: 用户输入的消息

        Returns:
            最终响应给用户的文本
        """
        logger.info(f"MainAgent[{self.session_id}] 处理消息: {message}")

        # 触发消息接收钩子
        hook_result = await self.hooks.on_message_receive(message, self.session_id)
        if hook_result.block:
            logger.debug(f"MainAgent[{self.session_id}] 消息被钩子阻止")
            return hook_result.modified_message or "消息处理被阻止"
        if hook_result.modified_message:
            message = hook_result.modified_message

        try:
            self.state.is_processing = True

            # 根据当前状态决定处理方式
            if self.state.current_task is None:
                response = await self._handle_new_message(message)
            else:
                response = await self._handle_existing_task(message)

            return response

        except Exception as e:
            logger.error(f"MainAgent[{self.session_id}] 处理消息失败: {e}", exc_info=True)
            await self._cleanup_task()
            return f"处理消息时发生错误: {str(e)}"
        finally:
            self.state.is_processing = False

    async def _handle_new_message(self, message: str) -> str:
        """处理新消息（无当前任务）"""
        logger.debug(f"MainAgent[{self.session_id}] 处理新消息")

        # 使用消息路由器识别消息类别
        category = self.message_router.get_category(message)
        logger.debug(f"MainAgent[{self.session_id}] 消息分类: {category}")

        # 根据类别分发处理
        if category in [
            MessageCategory.TASK_CREATE,
            MessageCategory.TASK_STATUS,
            MessageCategory.TASK_CANCEL,
            MessageCategory.TASK_COMPLETE,
            MessageCategory.TASK_LIST,
        ]:
            return await self._handle_task_message(category, message)
        elif category == MessageCategory.HELP:
            return await self._handle_help()
        elif category == MessageCategory.CONTROL:
            return await self._handle_control(message)
        else:  # CHAT 或 INQUIRY
            return await self._handle_chat_message(message)

    async def _handle_task_message(self, category: MessageCategory, message: str) -> str:
        """处理任务相关消息"""
        logger.debug(f"MainAgent[{self.session_id}] 处理任务消息: {category}")
        return self.workflow_manager.handle_task_message(category, message)

    async def _handle_chat_message(self, message: str) -> str:
        """处理对话消息"""
        logger.debug(f"MainAgent[{self.session_id}] 处理对话消息")

        # 触发规划前钩子
        hook_result = await self.hooks.before_planning(message)
        if hook_result.block:
            logger.debug(f"MainAgent[{self.session_id}] 规划被钩子阻止")
            return hook_result.modified_message or "任务规划被阻止"
        if hook_result.modified_message:
            message = hook_result.modified_message

        # 任务规划
        planning_result = await self._plan_task(message)
        await self.hooks.after_planning(planning_result)

        # 执行决策
        decision = await self._make_decision(
            "new_message", message=message, planning_result=planning_result
        )
        await self.hooks.after_decision(decision)

        # 执行决策
        response = await self._execute_decision(decision)

        return response

    async def _handle_task_request(self, message: str, decision: DecisionResult) -> str:
        """处理任务相关请求"""
        logger.debug(f"MainAgent[{self.session_id}] 处理任务请求: {message}")

        # 这里可以添加更复杂的任务处理逻辑
        # 对于简单的情况，我们可以返回一个友好的响应
        if "能力" in message or "help" in message.lower():
            capabilities = """我是 Nanobot，具备以下能力：

消息路由和分类：
- 智能识别消息类型（对话、任务管理、控制、帮助等）
- 自动路由消息到合适的处理器

工作流管理：
- 创建和管理工作流
- 任务状态跟踪
- 任务依赖管理
- 工作流暂停/恢复/完成/取消

任务执行：
- 任务规划和分解
- Subagent 调度和执行
- 任务结果聚合

上下文和记忆：
- 上下文构建和压缩
- 消息历史管理
- 长期记忆存储

命令行工具：
- 提供丰富的 CLI 命令
- 支持工作流、定时任务等操作

需要帮助？请输入"帮助"查看详细命令说明。"""
            return capabilities
        elif "创建" in message:
            return "任务创建功能已就绪，请提供任务描述。"
        elif "查看" in message or "状态" in message:
            return "任务状态查询功能已就绪，请提供任务 ID。"
        else:
            # 使用现有的 chat 处理逻辑
            return await self._handle_chat_message(message)

    async def _handle_help(self) -> str:
        """处理帮助请求"""
        logger.debug(f"MainAgent[{self.session_id}] 处理帮助请求")
        help_text = (
            "Nanobot 使用帮助：\n\n"
            "任务管理命令：\n"
            "- 创建任务 [任务描述]: 创建新任务\n"
            "- 查看任务 [任务ID]: 查询任务状态\n"
            "- 取消任务 [任务ID]: 取消指定任务\n"
            "- 完成任务 [任务ID]: 完成指定任务\n"
            "- 列出任务: 显示所有任务\n\n"
            "控制命令：\n"
            "- 继续: 恢复暂停的任务\n"
            "- 暂停: 暂停当前任务\n"
            "- 重试: 重试失败的任务\n\n"
            "其他命令：\n"
            "- 帮助: 显示此帮助信息\n"
        )
        return help_text

    async def _handle_control(self, message: str) -> str:
        """处理控制命令"""
        logger.debug(f"MainAgent[{self.session_id}] 处理控制命令: {message}")

        if "继续" in message or "恢复" in message:
            # 这里可以添加恢复任务的逻辑
            return "恢复任务功能将在未来版本中实现"
        elif "暂停" in message:
            # 这里可以添加暂停任务的逻辑
            return "暂停任务功能将在未来版本中实现"
        elif "重试" in message:
            # 这里可以添加重试任务的逻辑
            return "重试任务功能将在未来版本中实现"

        return "未知的控制命令"

    async def _handle_existing_task(self, message: str) -> str:
        """处理现有任务的消息"""
        logger.debug(f"MainAgent[{self.session_id}] 处理现有任务消息")

        # 检测是否是任务修正或取消
        # 注意：需要检查 task_planner 是否有这些方法
        if hasattr(self.task_planner, "cancellation_detector") and hasattr(
            self.task_planner.cancellation_detector, "is_cancellation"
        ):
            if await self.task_planner.cancellation_detector.is_cancellation(message):
                return await self._handle_task_cancellation()

        if hasattr(self.task_planner, "correction_detector") and hasattr(
            self.task_planner.correction_detector, "detect_correction"
        ):
            correction = await self.task_planner.correction_detector.detect_correction(
                message, None
            )
            if correction:
                return await self._handle_task_correction(message)

        # 如果不是取消或修正，直接当作新消息处理
        # 不需要清理当前任务，因为新消息应该能自然承接旧任务
        logger.info(f"MainAgent[{self.session_id}] 将消息作为新消息处理")
        return await self._handle_new_message(message)

    async def _plan_task(self, message: str):
        """规划任务"""
        # 构建上下文
        context, stats = await self.context_manager.build_context(self.session_id)
        self.state.context_stats = stats

        # 任务规划
        planning_result = await self.task_planner.plan_task(message, context)
        if isinstance(planning_result, TaskPlan):
            self.state.current_task = planning_result.task_type

        logger.debug(f"MainAgent[{self.session_id}] 任务规划结果: {planning_result}")
        return planning_result

    async def _make_decision(self, trigger: str, **kwargs) -> DecisionResult:
        """做出执行决策"""
        logger.debug(f"MainAgent[{self.session_id}] 做出决策，触发器: {trigger}")

        hook_result = await self.hooks.before_decision(trigger)
        if hook_result.block:
            logger.debug(f"MainAgent[{self.session_id}] 决策被钩子阻止")
            return DecisionResult(
                success=True, action="reply", message=hook_result.modified_message or "决策被阻止"
            )

        # 当处理新消息请求时，需要构建完整的 NewMessageRequest 结构
        if trigger == "new_message" and "message" in kwargs:
            import time
            from uuid import uuid4

            from nanobot.agent.decision.models import NewMessageRequest

            # 构建完整的 NewMessageRequest
            message_data = NewMessageRequest(
                message_id=str(uuid4()),
                content=kwargs["message"],
                sender_id="user",
                timestamp=time.time(),
                conversation_id=self.session_id,
                message_type="text",
            ).model_dump()
            request = DecisionRequest(
                request_type=trigger, data=message_data, context=kwargs.get("context")
            )
        else:
            request = DecisionRequest(
                request_type=trigger, data=kwargs, context=kwargs.get("context")
            )

        decision = await self.decision_maker.make_decision(request)
        logger.debug(f"MainAgent[{self.session_id}] 决策结果: {decision}")

        return decision

    async def _execute_decision(self, decision: DecisionResult) -> str:
        """执行决策"""
        logger.debug(f"MainAgent[{self.session_id}] 执行决策: {decision.action}")

        if decision.action == "reply":
            return await self._handle_reply_decision(decision)

        if decision.action == "spawn_subagent":
            return await self._handle_spawn_subagent_decision(decision)

        if decision.action == "await_result":
            return await self._handle_await_result_decision(decision)

        if decision.action == "complete_task":
            return await self._handle_complete_task_decision(decision)

        if decision.action == "create_task":
            # 对于创建任务的决策，实际执行任务处理
            content = decision.data.get("content", "")
            return await self._handle_task_request(content, decision)

        if decision.action == "cancel_task":
            return await self._handle_task_cancellation()

        if decision.action == "handle_correction":
            correction_content = decision.data.get("content", "")
            return await self._handle_task_correction(correction_content)

        if decision.action == "simple_query":
            # 对于简单查询，实际处理查询
            content = decision.data.get("content", "")
            return await self._handle_task_request(content, decision)

        logger.warning(f"MainAgent[{self.session_id}] 未知决策类型: {decision.action}")
        return "无法理解的决策类型"

    async def _handle_reply_decision(self, decision: DecisionResult) -> str:
        """处理回复决策"""
        response = decision.message or "已处理您的请求"
        await self.hooks.on_response_send(response, self.session_id)
        await self._cleanup_task()
        return response

    async def _handle_spawn_subagent_decision(self, decision: DecisionResult) -> str:
        """处理生成 Subagent 决策"""
        if not decision.data.get("subagent_task"):
            logger.error(f"MainAgent[{self.session_id}] 生成 Subagent 决策缺少任务描述")
            return "无法执行任务：缺少任务描述"

        # 创建 Subagent 任务
        task = SubagentTask(
            task_id=str(uuid4()),
            description=decision.data.get("subagent_task"),
            config=decision.data.get("subagent_config") or {},
            agent_type=decision.data.get("subagent_config", {}).get("agent_type"),
            skills=decision.data.get("subagent_config", {}).get("skills"),
        )

        # 触发 Subagent 生成钩子
        await self.hooks.on_subagent_spawn(task.task_id, task)

        # 调度 Subagent
        await self.subagent_manager.spawn_subagent(task)
        self.state.subagent_tasks[task.task_id] = task
        self.state.subagent_states[task.task_id] = SubagentState(
            task_id=task.task_id, status="ASSIGNED", progress=0.0
        )

        logger.info(f"MainAgent[{self.session_id}] 已生成 Subagent: {task.task_id}")

        return f"正在执行任务：{task.description}"

    async def _handle_await_result_decision(self, decision: DecisionResult) -> str:
        """处理等待结果决策"""
        # 检查是否有正在运行的 Subagent
        running_tasks = [
            task_id
            for task_id, state in self.state.subagent_states.items()
            if state.status in ["ASSIGNED", "RUNNING"]
        ]

        if running_tasks:
            return "任务正在执行中，请稍候..."
        else:
            return await self._aggregate_responses()

    async def _handle_complete_task_decision(self, decision: DecisionResult) -> str:
        """处理完成任务决策"""
        response = decision.message or await self._aggregate_responses()
        await self.hooks.on_response_send(response, self.session_id)
        await self._cleanup_task()
        return response

    async def _handle_subagent_result(self, result: SubagentResult) -> str:
        """处理 Subagent 结果"""
        logger.info(f"MainAgent[{self.session_id}] 收到 Subagent 结果: {result.task_id}")

        self.state.subagent_results[result.task_id] = result
        self.state.subagent_states[result.task_id] = result.state

        # 触发 Subagent 结果钩子
        await self.hooks.on_subagent_result(result)

        # 决策下一步动作
        decision = await self._make_decision("subagent_result", result=result)
        await self.hooks.after_decision(decision)

        # 执行决策
        response = await self._execute_decision(decision)
        return response

    async def _handle_task_cancellation(self) -> str:
        """处理任务取消"""
        logger.info(f"MainAgent[{self.session_id}] 任务取消")

        # 取消所有 Subagent
        for task_id in list(self.state.subagent_tasks.keys()):
            await self.subagent_manager.cancel_subagent(task_id)

        await self.hooks.on_task_cancelled(self.state.current_task)
        await self._cleanup_task()

        return "任务已取消"

    async def _handle_task_correction(self, correction: str) -> str:
        """处理任务修正"""
        logger.info(f"MainAgent[{self.session_id}] 任务修正: {correction}")

        # 取消当前任务
        for task_id in list(self.state.subagent_tasks.keys()):
            await self.subagent_manager.cancel_subagent(task_id)

        # 重新规划任务
        self.state.current_task = None
        return await self._handle_new_message(correction)

    async def _handle_subagent_interrupt(self, message: str) -> str:
        """处理 Subagent 中断"""
        logger.info(f"MainAgent[{self.session_id}] 处理 Subagent 中断: {message}")

        # 中断所有正在运行的 Subagent
        for task_id in list(self.state.subagent_tasks.keys()):
            await self.subagent_manager.interrupt_subagent(task_id, message)

        await self.hooks.on_subagent_interrupt(message)
        return "任务已中断，正在重新评估..."

    async def _aggregate_responses(self) -> str:
        """聚合 Subagent 响应"""
        logger.debug(f"MainAgent[{self.session_id}] 聚合 Subagent 响应")

        # 聚合所有 Subagent 结果
        results = list(self.state.subagent_results.values())
        if not results:
            return "任务已完成，但未获得任何结果"

        # 简单的结果聚合（可以根据需要扩展）
        aggregated = []
        for result in results:
            if hasattr(result, "output"):
                aggregated.append(f"任务 {result.task_id} 结果:\n{result.output}")
            elif hasattr(result, "result"):
                aggregated.append(f"任务 {result.task_id} 结果:\n{result.result}")
            else:
                aggregated.append(f"任务 {result.task_id} 已完成")

        return "\n\n".join(aggregated)

    async def _cleanup_task(self) -> None:
        """清理任务状态"""
        self.state.current_task = None
        self.state.subagent_tasks.clear()
        self.state.subagent_results.clear()
        self.state.subagent_states.clear()
        self.state.context_stats = None

    async def get_status(self) -> Dict[str, Any]:
        """获取 MainAgent 状态"""
        return {
            "session_id": self.session_id,
            "current_task": self.state.current_task,
            "subagent_count": len(self.state.subagent_tasks),
            "running_count": len(
                [
                    state
                    for state in self.state.subagent_states.values()
                    if state.status in ["ASSIGNED", "RUNNING"]
                ]
            ),
            "context_stats": self.state.context_stats.dict() if self.state.context_stats else None,
        }
