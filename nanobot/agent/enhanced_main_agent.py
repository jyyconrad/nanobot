"""
Enhanced MainAgent - 增强版主代理

改进点：
1. 集成 SkillLoader，支持动态技能加载
2. 提供配置查询工具（获取 skills、agents）
3. 智能决策：自动选择 skills 并分配给 subagent
4. Subagent 创建时传递 skills 信息
5. AgnoSubagent 内部通过 SkillLoader 加载技能详细内容
"""

import logging
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel

from nanobot.agent.context_manager import ContextManager, ContextStats
from nanobot.agent.decision.decision_maker import ExecutionDecisionMaker
from nanobot.agent.decision.models import DecisionRequest, DecisionResult
from nanobot.agent.decision.skill_decision_handler import SkillDecisionHandler
from nanobot.agent.hooks import MainAgentHooks
from nanobot.agent.planner.models import TaskPlan
from nanobot.agent.planner.task_planner import TaskPlanner
from nanobot.agent.skill_loader import SkillLoader
from nanobot.agent.subagent.manager import SubagentManager
from nanobot.agent.subagent.models import SubagentResult, SubagentState, SubagentTask
from nanobot.agent.tools.config_tools import (
    GetAvailableAgentsTool,
    GetAvailableSkillsTool,
    GetSkillContentTool,
    GetSkillsForTaskTool,
)
from nanobot.agent.tools.registry import ToolRegistry
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


class EnhancedMainAgent:
    """
    Enhanced MainAgent - 增强版主代理

    改进的功能：
    - 智能决策：调用工具查询配置，自动选择 skills
    - 动态技能分配：根据任务类型分配给 subagent
    - 配置透明：可以查询可用 skills 和 agents
    """

    def __init__(self, session_id: str = None):
        if session_id is None:
            session_id = str(uuid4())

        self.session_id = session_id
        self.state = MainAgentState(session_id=session_id)

        # 核心组件
        self.context_manager = ContextManager()
        self.task_planner = TaskPlanner()

        # 🔥 新增：SkillLoader
        self.skill_loader = SkillLoader()
        logger.info(f"EnhancedMainAgent[{session_id}] SkillLoader 已初始化")

        # 🔥 新增：工具注册表，包含配置查询工具
        self.tool_registry = ToolRegistry()
        self._register_config_tools()
        logger.info(
            f"EnhancedMainAgent[{session_id}] 工具注册表已初始化，已注册 {len(self.tool_registry)} 个工具"
        )

        # 决策管理器（需要 agent_loop，暂时传 None）
        self.decision_maker = ExecutionDecisionMaker(None)

        # 🔥 新增：技能决策处理器
        self.skill_decision_handler = SkillDecisionHandler(
            agent_loop=None, tool_registry=self.tool_registry, skill_loader=self.skill_loader
        )
        logger.info(f"EnhancedMainAgent[{session_id}] SkillDecisionHandler 已初始化")

        self.subagent_manager = SubagentManager()
        self.hooks = MainAgentHooks()
        self.message_router = MessageRouter()
        self.workflow_manager = WorkflowManager()

        logger.info(f"EnhancedMainAgent[{session_id}] 初始化完成")

    def _register_config_tools(self):
        """注册配置查询工具"""
        self.tool_registry.register(GetAvailableSkillsTool())
        self.tool_registry.register(GetSkillsForTaskTool())
        self.tool_registry.register(GetAvailableAgentsTool())
        self.tool_registry.register(GetSkillContentTool())

    async def process_message(self, message: str) -> str:
        """
        处理用户消息的主要入口

        Args:
            message: 用户输入的消息

        Returns:
            最终响应给用户的文本
        """
        logger.info(f"EnhancedMainAgent[{self.session_id}] 处理消息: {message}")

        # 触发消息接收钩子
        hook_result = await self.hooks.on_message_receive(message, self.session_id)
        if hook_result.block:
            logger.debug(f"EnhancedMainAgent[{self.session_id}] 消息被钩子阻止")
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
            logger.error(f"EnhancedMainAgent[{self.session_id}] 处理消息失败: {e}", exc_info=True)
            await self._cleanup_task()
            return f"处理消息时发生错误: {str(e)}"
        finally:
            self.state.is_processing = False

    async def _handle_new_message(self, message: str) -> str:
        """处理新消息（无当前任务）"""
        logger.debug(f"EnhancedMainAgent[{self.session_id}] 处理新消息")

        # 使用消息路由器识别消息类别
        category = self.message_router.get_category(message)
        logger.debug(f"EnhancedMainAgent[{self.session_id}] 消息分类: {category}")

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

    async def _handle_chat_message(self, message: str) -> str:
        """处理对话消息"""
        logger.debug(f"EnhancedMainAgent[{self.session_id}] 处理对话消息")

        # 触发规划前钩子
        hook_result = await self.hooks.before_planning(message)
        if hook_result.block:
            logger.debug(f"EnhancedMainAgent[{self.session_id}] 规划被钩子阻止")
            return hook_result.modified_message or "任务规划被阻止"
        if hook_result.modified_message:
            message = hook_result.modified_message

        # 任务规划
        planning_result = await self._plan_task(message)
        await self.hooks.after_planning(planning_result)

        # 🔥 使用智能技能决策
        decision = await self._make_skill_decision(message)
        await self.hooks.after_decision(decision)

        # 执行决策
        response = await self._execute_decision(decision)

        return response

    async def _make_skill_decision(self, message: str) -> DecisionResult:
        """
        使用 SkillDecisionHandler 进行智能决策

        Args:
            message: 用户消息

        Returns:
            决策结果
        """
        logger.info(f"EnhancedMainAgent[{self.session_id}] 开始智能技能决策")

        # 构建决策请求
        import time

        request = DecisionRequest(
            request_type="skill_decision",
            data={
                "message_id": str(uuid4()),
                "content": message,
                "sender_id": "user",
                "timestamp": time.time(),
                "conversation_id": self.session_id,
                "message_type": "text",
            },
            context={"session_id": self.session_id},
        )

        # 调用技能决策处理器
        decision = await self.skill_decision_handler.handle_request(request)

        logger.info(f"EnhancedMainAgent[{self.session_id}] 智能决策完成: {decision.action}")
        return decision

    async def _execute_decision(self, decision: DecisionResult) -> str:
        """执行决策"""
        logger.debug(f"EnhancedMainAgent[{self.session_id}] 执行决策: {decision.action}")

        if decision.action == "reply":
            return await self._handle_reply_decision(decision)

        if decision.action == "spawn_subagent":
            return await self._handle_spawn_subagent_decision(decision)

        if decision.action == "error":
            return decision.message or "决策执行失败"

        logger.warning(f"EnhancedMainAgent[{self.session_id}] 未知决策类型: {decision.action}")
        return "无法理解的决策类型"

    async def _handle_spawn_subagent_decision(self, decision: DecisionResult) -> str:
        """
        处理生成 Subagent 决策（增强版）

        重点：确保 skills 信息被正确传递
        """
        if not decision.data.get("subagent_task"):
            logger.error(f"EnhancedMainAgent[{self.session_id}] 生成 Subagent 决策缺少任务描述")
            return "无法执行任务：缺少任务描述"

        subagent_config = decision.data.get("subagent_config", {})
        logger.info(
            f"EnhancedMainAgent[{self.session_id}] Subagent 配置: {subagent_config}"
        )

        # 创建 Subagent 任务
        task = SubagentTask(
            task_id=str(uuid4()),
            description=decision.data.get("subagent_task"),
            config=subagent_config,
            agent_type=subagent_config.get("agent_type"),
            skills=subagent_config.get("skills"),  # 🔥 关键：传递 skills
        )

        logger.info(
            f"EnhancedMainAgent[{self.session_id}] 创建 Subagent: "
            f"task_id={task.task_id}, "
            f"agent_type={task.agent_type}, "
            f"skills={task.skills}"
        )

        # 触发 Subagent 生成钩子
        await self.hooks.on_subagent_spawn(task.task_id, task)

        # 调度 Subagent
        await self.subagent_manager.spawn_subagent(task)
        self.state.subagent_tasks[task.task_id] = task
        self.state.subagent_states[task.task_id] = SubagentState(
            task_id=task.task_id, status="ASSIGNED", progress=0.0
        )

        logger.info(f"EnhancedMainAgent[{self.session_id}] 已生成 Subagent: {task.task_id}")

        return f"正在执行任务：{task.description}（使用技能: {', '.join(task.skills or [])}）"

    async def _handle_reply_decision(self, decision: DecisionResult) -> str:
        """处理回复决策"""
        response = decision.message or "已处理您的请求"
        await self.hooks.on_response_send(response, self.session_id)
        await self._cleanup_task()
        return response

    # 以下方法保持原样（从 MainAgent 复制）
    async def _handle_task_message(self, category: MessageCategory, message: str) -> str:
        """处理任务相关消息"""
        logger.debug(f"EnhancedMainAgent[{self.session_id}] 处理任务消息: {category}")
        return self.workflow_manager.handle_task_message(category, message)

    async def _handle_help(self) -> str:
        """处理帮助请求"""
        logger.debug(f"EnhancedMainAgent[{self.session_id}] 处理帮助请求")
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
        logger.debug(f"EnhancedMainAgent[{self.session_id}] 处理控制命令: {message}")

        if "继续" in message or "恢复" in message:
            return "恢复任务功能将在未来版本中实现"
        elif "暂停" in message:
            return "暂停任务功能将在未来版本中实现"
        elif "重试" in message:
            return "重试任务功能将在未来版本中实现"

        return "未知的控制命令"

    async def _handle_existing_task(self, message: str) -> str:
        """处理现有任务的消息"""
        logger.debug(f"EnhancedMainAgent[{self.session_id}] 处理现有任务消息")

        # 检测是否是任务修正或取消
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
        logger.info(f"EnhancedMainAgent[{self.session_id}] 将消息作为新消息处理")
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

        logger.debug(f"EnhancedMainAgent[{self.session_id}] 任务规划结果: {planning_result}")
        return planning_result

    async def _handle_task_cancellation(self) -> str:
        """处理任务取消"""
        logger.info(f"EnhancedMainAgent[{self.session_id}] 任务取消")

        # 取消所有 Subagent
        for task_id in list(self.state.subagent_tasks.keys()):
            await self.subagent_manager.cancel_subagent(task_id)

        await self.hooks.on_task_cancelled(self.state.current_task)
        await self._cleanup_task()

        return "任务已取消"

    async def _handle_task_correction(self, correction: str) -> str:
        """处理任务修正"""
        logger.info(f"EnhancedMainAgent[{self.session_id}] 任务修正: {correction}")

        # 取消当前任务
        for task_id in list(self.state.subagent_tasks.keys()):
            await self.subagent_manager.cancel_subagent(task_id)

        # 重新规划任务
        self.state.current_task = None
        return await self._handle_new_message(correction)

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

    def get_tool_registry(self) -> ToolRegistry:
        """获取工具注册表"""
        return self.tool_registry
