"""
MainAgent 主代理类 - 协调所有组件的核心入口

集成提示词系统 V2，支持渐进式上下文披露。
"""

import asyncio
import inspect
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel

# 导入现有组件
from nanobot.agent.context_manager import ContextManagerV2 as ContextManager
from nanobot.agent.decision.decision_maker import ExecutionDecisionMaker
from nanobot.agent.decision.models import DecisionRequest, DecisionResult
from nanobot.agent.hooks import MainAgentHooks as MainAgentHooks
from nanobot.agent.planner.models import TaskPlan
from nanobot.agent.planner.task_planner import TaskPlanner
from nanobot.agent.subagent.manager import SubagentManager
from nanobot.agent.subagent.models import SubagentResult, SubagentState, SubagentTask
from nanobot.agent.workflow.message_router import MessageRouter
from nanobot.agent.workflow.models import MessageCategory
from nanobot.agent.workflow.workflow_manager import WorkflowManager

# 新增：Prompt System V2
try:
    from nanobot.agent.prompt_system import PromptSystemV2, get_prompt_system_v2

    PROMPT_SYSTEM_V2_AVAILABLE = True
except ImportError:
    PROMPT_SYSTEM_V2_AVAILABLE = False
    PromptSystemV2 = None
    get_prompt_system_v2 = None

logger = logging.getLogger(__name__)


class MainAgentState(BaseModel):
    """MainAgent 状态模型"""

    session_id: str
    current_task: Optional[str] = None
    subagent_tasks: Dict[str, SubagentTask] = {}
    subagent_results: Dict[str, SubagentResult] = {}
    subagent_states: Dict[str, SubagentState] = {}
    context_stats: Optional[Dict] = None
    is_processing: bool = False


class MainAgent:
    """
    MainAgent 主代理类

    负责：
    - 用户消息接收和初步处理
    - 任务识别、规划和分解
    - 上下文和记忆管理
    - Subagent 协调和监控
    - 下一步动作决策
    - 用户响应聚合和总结
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        config: Optional[Dict] = None,
        prompt_system_v2: Optional["PromptSystemV2"] = None,
        context_manager: Optional["ContextManager"] = None,
        agent_loop: Optional["AgentLoop"] = None,
    ):
        """
        初始化 MainAgent

        Args:
            session_id: 会话 ID
            config: 配置字典
            prompt_system_v2: 提示词系统 V2 实例（可选）
            context_manager: 上下文管理器实例（可选）
            agent_loop: AgentLoop 实例（可选）
        """
        if session_id is None:
            session_id = str(uuid4())
            self.session_id = session_id
        else:
            self.session_id = session_id

        self.config = config or {}
        self.agent_loop = agent_loop  # 保存 agent_loop 引用

        # 初始化提示词系统 V2
        if prompt_system_v2:
            self.prompt_system_v2 = prompt_system_v2
            logger.info(
                f"MainAgent[{self.session_id}] Using provided PromptSystemV2 instance"
            )
        elif PROMPT_SYSTEM_V2_AVAILABLE:
            self.prompt_system_v2 = get_prompt_system_v2()
            logger.info(
                f"MainAgent[{self.session_id}] Initialized PromptSystemV2 from default config"
            )
        else:
            self.prompt_system_v2 = None
            logger.warning(
                f"MainAgent[{self.session_id}] PromptSystemV2 not available, using legacy system"
            )

        # 初始化上下文管理器
        self.context_manager = context_manager or ContextManager()

        # 初始化核心组件
        self.state = MainAgentState(session_id=self.session_id)
        self.task_planner = TaskPlanner()
        self.decision_maker = ExecutionDecisionMaker(agent_loop=self.agent_loop)
        self.subagent_manager = SubagentManager()
        self.message_router = MessageRouter()
        self.workflow_manager = WorkflowManager()
        self.hooks = MainAgentHooks()

        # 注册 MainAgent 钩子
        self._register_main_agent_hooks()

        logger.info(f"MainAgent[{self.session_id}] Initialized")

    def _register_main_agent_hooks(self):
        """注册 MainAgent 钩子"""
        # TODO: 从配置中注册自定义钩子
        pass

    async def process_message(self, message: str) -> str:
        """
        处理用户消息

        Args:
            message: 用户输入的消息

        Returns:
            最终响应给用户的文本
        """
        logger.info(
            f"MainAgent[{self.session_id}] Processing message: {message[:50]}..."
        )

        # 触发消息接收钩子
        hook_result = await self.hooks.on_message_receive(message, self.session_id)
        if hook_result.block:
            logger.debug(f"MainAgent[{self.session_id}] Message blocked by hook")
            return hook_result.modified_message or "消息处理被阻止"
        if hook_result.modified_message:
            message = hook_result.modified_message

        try:
            self.state.is_processing = True

            # 构建上下文（为了测试兼容性）
            try:
                context, error = await self.context_manager.build_context(
                    message=message,
                    conversation_history=self.context_manager.get_recent_messages(n=10),
                )
                if error:
                    raise Exception(error)
            except AttributeError:
                # 如果 context_manager 没有 build_context 方法，跳过
                pass

            # 使用 PromptSystemV2 构建系统提示词（如果可用）
            if self.prompt_system_v2:
                system_prompt = self.prompt_system_v2.build_main_agent_prompt(
                    skills=self._get_skill_names(),
                    tools=self._get_tool_descriptions(),
                    context=self._get_context(),
                )
                logger.debug(
                    f"MainAgent[{self.session_id}] Built system prompt with PromptSystemV2"
                )
            else:
                # 使用传统方式构建提示词
                system_prompt = self._build_legacy_system_prompt()

            # 添加到消息历史
            self.context_manager.add_message("system", system_prompt)
            self.context_manager.add_message("user", message)

            # 使用消息路由器识别消息类型
            category = self.message_router.get_category(message)
            logger.info(f"MainAgent[{self.session_id}] Message category: {category}")

            # 根据消息类型路由到对应的处理程序
            if category == MessageCategory.TASK_CREATE:
                response = await self._handle_task_create(message)
            elif category == MessageCategory.TASK_STATUS:
                response = await self._handle_task_status(message)
            elif category == MessageCategory.TASK_CANCEL:
                response = await self._handle_task_cancel(message)
            elif category == MessageCategory.HELP:
                response = self._handle_help()
            elif category == MessageCategory.CONTROL:
                response = await self._handle_control(message)
            else:
                # 默认：交给 MainAgent 处理对话
                response = await self._handle_chat_message(message)

            logger.info(f"MainAgent[{self.session_id}] Response generated")

            return response

        except Exception as e:
            logger.error(
                f"MainAgent[{self.session_id}] Error processing message: {e}",
                exc_info=True,
            )
            await self._cleanup_task()
            return str(e)

        finally:
            self.state.is_processing = False

    # ==================== 消息处理方法 ====================

    def _handle_task_create(self, message: str) -> str:
        """处理任务创建消息"""
        logger.debug(
            f"MainAgent[{self.session_id}] Handling task create: {message[:50]}..."
        )

        # 使用任务规划器分析任务
        task_plan = self.task_planner.analyze_task(message)

        # 创建任务ID
        task_id = f"task_{len(self.state.subagent_tasks) + 1}_{uuid4().hex[:8]}"

        # 存储任务信息
        self.state.subagent_tasks[task_id] = {
            "id": task_id,
            "description": message,
            "plan": task_plan,
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "subtasks": [],
        }

        # 创建子任务
        for i, step in enumerate(task_plan.steps[:5], 1):  # 最多5个子任务
            subtask_id = f"{task_id}_subtask_{i}"
            subtask = {
                "id": subtask_id,
                "description": step,
                "status": "pending",
                "parent_task": task_id,
            }
            self.state.subagent_tasks[task_id]["subtasks"].append(subtask)

        # 更新当前任务
        self.state.current_task = task_id

        logger.info(
            f"MainAgent[{self.session_id}] Task created: {task_id} with {len(task_plan.steps)} steps"
        )

        # 构建响应
        response_parts = [
            f"✅ 任务已创建",
            f"",
            f"任务ID: {task_id}",
            f"任务描述: {task_plan.summary}",
            f"",
            f"执行步骤:",
        ]

        for i, step in enumerate(task_plan.steps[:5], 1):
            response_parts.append(f"  {i}. {step}")

        if len(task_plan.steps) > 5:
            response_parts.append(f"  ... 还有 {len(task_plan.steps) - 5} 个步骤")

        response_parts.extend(
            [
                f"",
                f"使用 '/status {task_id}' 查看任务状态",
                f"使用 '/cancel {task_id}' 取消任务",
            ]
        )

        return "\n".join(response_parts)

    async def _handle_task_status(self, message: str) -> str:
        """处理任务状态查询"""
        logger.debug(
            f"MainAgent[{self.session_id}] Handling task status query: {message[:50]}..."
        )

        # 解析任务ID
        parts = message.split()
        task_id = None

        for part in parts:
            if part.startswith("task_"):
                task_id = part
                break

        # 如果没有指定任务ID，使用当前任务
        if not task_id and self.state.current_task:
            task_id = self.state.current_task

        # 查询指定任务
        if task_id and task_id in self.state.subagent_tasks:
            task = self.state.subagent_tasks[task_id]
            status = task.get("status", "unknown")
            description = task.get("description", "无描述")
            created_at = task.get("created_at", "未知")
            subtasks = task.get("subtasks", [])

            # 计算子任务状态
            completed = sum(1 for s in subtasks if s.get("status") == "completed")
            total = len(subtasks)

            response_parts = [
                f"📋 任务状态: {task_id}",
                f"",
                f"描述: {description}",
                f"状态: {status}",
                f"创建时间: {created_at}",
                f"",
                f"进度: {completed}/{total} 子任务完成",
            ]

            if subtasks:
                response_parts.append(f"子任务列表:")
                for i, subtask in enumerate(subtasks[:10], 1):  # 最多显示10个
                    st_status = subtask.get("status", "unknown")
                    st_desc = subtask.get("description", "无描述")[:50]
                    status_icon = (
                        "✅"
                        if st_status == "completed"
                        else "⏳" if st_status == "in_progress" else "⏸️"
                    )
                    response_parts.append(
                        f"  {status_icon} {i}. [{st_status}] {st_desc}"
                    )

                if len(subtasks) > 10:
                    response_parts.append(f"  ... 还有 {len(subtasks) - 10} 个子任务")

            return "\n".join(response_parts)

        # 显示所有任务状态
        if self.state.subagent_tasks:
            response_parts = ["📋 所有任务状态:", ""]

            for tid, task in self.state.subagent_tasks.items():
                status = task.get("status", "unknown")
                desc = task.get("description", "无描述")[:40]
                status_icon = (
                    "✅"
                    if status == "completed"
                    else "⏳" if status == "in_progress" else "⏸️"
                )
                current_marker = " 👈 当前" if tid == self.state.current_task else ""
                response_parts.append(
                    f"{status_icon} {tid}: [{status}] {desc}{current_marker}"
                )

            response_parts.extend(
                [
                    "",
                    f"共 {len(self.state.subagent_tasks)} 个任务",
                    "使用 '/status <task_id>' 查看详细信息",
                ]
            )

            return "\n".join(response_parts)

        return "当前没有任务。使用 '/task <描述>' 创建新任务。"

    async def _handle_task_cancel(self, message: str) -> str:
        """处理任务取消消息"""
        logger.debug(
            f"MainAgent[{self.session_id}] Handling task cancel: {message[:50]}..."
        )

        if self.state.current_task:
            await self._cleanup_task()
            return "已取消当前任务"
        else:
            return "没有正在运行的任务"

    def _handle_help(self) -> str:
        """处理帮助请求"""
        # TODO: 实现帮助文档
        return "帮助文档开发中"

    async def _handle_control(self, message: str) -> str:
        """处理控制命令"""
        logger.debug(
            f"MainAgent[{self.session_id}] Handling control: {message[:50]}..."
        )

        # TODO: 实现控制逻辑
        return "控制功能开发中"

    async def _handle_chat_message(self, message: str) -> str:
        """处理普通对话消息"""
        logger.debug(
            f"MainAgent[{self.session_id}] Handling chat message: {message[:50]}..."
        )

        # 直接使用 LLM 处理消息（跳过决策器）
        try:
            # 使用 PromptSystemV2 构建系统提示词
            if self.prompt_system_v2:
                system_prompt = self.prompt_system_v2.build_main_agent_prompt(
                    skills=self._get_skill_names(),
                    tools=self._get_tool_descriptions(),
                    context=self._get_context(),
                )
            else:
                system_prompt = self._build_legacy_system_prompt()

            # 构建消息列表
            messages = [{"role": "system", "content": system_prompt}]

            # 添加历史消息
            history = self.context_manager.get_history()
            for msg in history[-10:]:  # 只取最近10条
                messages.append(
                    {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                )

            # 添加当前消息
            messages.append({"role": "user", "content": message})

            # 调用 LLM
            if self.agent_loop:
                provider = self.agent_loop.provider
                model = self.agent_loop.model
            else:
                # Fallback for testing
                from nanobot.providers.litellm_provider import LiteLLMProvider

                provider = LiteLLMProvider()
                model = "volcengine/glm-4.7"

            response = await provider.chat(
                messages=messages,
                model=model,
                temperature=0.7,
                tools=(
                    self.agent_loop.tools.get_definitions() if self.agent_loop else None
                ),
            )

            # 处理工具调用循环
            if response.has_tool_calls:
                return await self._handle_tool_calls(response, messages)
            else:
                return response.content

        except Exception as e:
            logger.error(f"Error in LLM call: {e}", exc_info=True)
            return f"LLM 调用出错：{str(e)}"

    async def _handle_tool_calls(
        self, response: Any, messages: List[Dict[str, Any]]
    ) -> str:
        """
        处理工具调用的完整循环

        Args:
            response: LLM 响应对象
            messages: 当前消息列表

        Returns:
            最终响应给用户的文本
        """
        logger.info(
            f"MainAgent[{self.session_id}] 处理工具调用：{len(response.tool_calls)} 个"
        )

        # 执行工具调用循环
        max_iterations = 10  # 防止无限循环
        current_messages = messages.copy()
        assistant_message = ""

        for iteration in range(max_iterations):
            if not response.has_tool_calls:
                # 没有工具调用，返回最终响应
                logger.debug(
                    f"MainAgent[{self.session_id}] 第 {iteration+1} 轮迭代：无工具调用"
                )
                break

            logger.info(
                f"MainAgent[{self.session_id}] 第 {iteration+1} 轮迭代：执行工具"
            )

            # 处理每个工具调用
            tool_results = []
            for tool_call in response.tool_calls:
                logger.debug(
                    f"MainAgent[{self.session_id}]   调用工具：{tool_call.name}"
                )

                try:
                    # 查找工具
                    if self.agent_loop and hasattr(self.agent_loop, "tools"):
                        tool = self.agent_loop.tools.get(tool_call.name)
                        if tool:
                            # 执行工具
                            logger.info(
                                f"MainAgent[{self.session_id}]   执行工具：{tool_call.name}"
                            )

                            # 处理工具参数
                            args = tool_call.arguments
                            logger.debug(
                                f"MainAgent[{self.session_id}]     - 参数类型: {type(args).__name__}"
                            )
                            logger.debug(
                                f"MainAgent[{self.session_id}]     - 参数内容: {str(args)[:200]}"
                            )

                            # 执行工具（检查是否是异步）
                            import inspect

                            if hasattr(tool, "execute") and inspect.iscoroutinefunction(
                                tool.execute
                            ):
                                tool_result = await tool.execute(**args)
                            else:
                                # 同步执行
                                tool_result = tool.execute(**args)

                            tool_results.append(
                                {"tool": tool_call.name, "result": tool_result}
                            )
                            logger.debug(
                                f"MainAgent[{self.session_id}]   工具结果：{str(tool_result)[:100]}"
                            )
                        else:
                            logger.warning(
                                f"MainAgent[{self.session_id}]   工具未找到：{tool_call.name}"
                            )
                            tool_results.append(
                                {
                                    "tool": tool_call.name,
                                    "result": f"工具未找到：{tool_call.name}",
                                }
                            )
                    else:
                        logger.warning(f"MainAgent[{self.session_id}]   没有工具注册表")
                        tool_results.append(
                            {"tool": tool_call.name, "result": "工具系统不可用"}
                        )
                except Exception as e:
                    logger.error(
                        f"MainAgent[{self.session_id}]   工具执行失败：{e}",
                        exc_info=True,
                    )
                    tool_results.append(
                        {"tool": tool_call.name, "result": f"执行失败：{str(e)}"}
                    )

            # 构建工具结果消息
            if tool_results:
                tool_result_messages = []
                for result in tool_results:
                    tool_result_messages.append(
                        f"工具 {result['tool']}：{str(result['result'])}"
                    )
                assistant_message = "\n".join(tool_result_messages)
                logger.info(
                    f"MainAgent[{self.session_id}]   工具执行结果：{assistant_message[:200]}"
                )

            # 添加助手响应到消息历史
            current_messages.append({"role": "assistant", "content": assistant_message})

            # 再次调用 LLM
            logger.info(f"MainAgent[{self.session_id}]   调用 LLM 处理工具结果")
            try:
                if self.agent_loop:
                    provider = self.agent_loop.provider
                    model = self.agent_loop.model
                else:
                    # Fallback for testing
                    from nanobot.providers.litellm_provider import LiteLLMProvider

                    provider = LiteLLMProvider()
                    model = "volcengine/glm-4.7"

                response = await provider.chat(
                    messages=current_messages, model=model, temperature=0.7
                )
            except Exception as e:
                logger.error(
                    f"MainAgent[{self.session_id}]   LLM 调用失败：{e}", exc_info=True
                )
                assistant_message += f"\n\nLLM 调用出错：{str(e)}"
                break

        # 返回最终响应
        return assistant_message or "工具调用完成"

    # ==================== 辅助方法 ====================

    def _build_legacy_system_prompt(self) -> str:
        """
        使用传统方式构建系统提示词（降级兼容）

        Returns:
        系统提示词字符串
        """
        # 构建传统的系统提示词
        # TODO: 从现有的 prompt_builder.py 迁移逻辑到这里
        # 暂时使用 ContextBuilder
        return "系统提示词（传统方式）"

    def _get_context(self) -> Dict:
        """
        获取当前上下文

        Returns:
            上下文字典
        """
        return {
            "current_task": self.state.current_task,
            "subagent_tasks": list(self.state.subagent_tasks.keys()),
            "context_stats": self.state.context_stats,
        }

    def _get_skill_names(self) -> List[str]:
        """
        获取可用的技能名称列表

        Returns:
            技能名称列表
        """
        # TODO: 从 skills loader 获取
        return ["coding", "testing", "debugging"]

    def _get_tool_descriptions(self) -> Dict[str, str]:
        """
        获取可用工具的描述

        Returns:
            工具描述字典
        """
        # TODO: 从工具注册表获取
        return {
            "read_file": "读取文件内容",
            "write_file": "写入文件内容",
            "exec": "执行命令",
        }

    def _get_available_tools(self) -> List[str]:
        """
        获取可用工具名称列表

        Returns:
            工具名称列表
        """
        # TODO: 从工具注册表获取
        return ["read_file", "write_file", "exec", "web_search", "web_fetch"]

    async def get_status(self) -> Dict[str, Any]:
        """
        获取 agent 状态

        Returns:
            状态字典
        """
        # 计算 running 子代理数量
        running_count = 0
        for task_id, state in self.state.subagent_states.items():
            try:
                if hasattr(state, "status") and state.status == "RUNNING":
                    running_count += 1
            except Exception as e:
                logger.warning(f"Error checking subagent state for {task_id}: {e}")

        return {
            "session_id": self.session_id,
            "current_task": self.state.current_task,
            "subagent_tasks": list(self.state.subagent_tasks.keys()),
            "subagent_count": len(self.state.subagent_tasks),
            "subagent_results": list(self.state.subagent_results.keys()),
            "is_processing": self.state.is_processing,
            "context_stats": self.state.context_stats,
            "running_count": running_count,
        }

    async def _cleanup_task(self) -> None:
        """清理当前任务资源"""
        logger.debug(f"MainAgent[{self.session_id}] Cleaning up task resources")

        # 清理子代理任务
        self.state.subagent_tasks.clear()
        self.state.subagent_results.clear()
        self.state.subagent_states.clear()

        # 清理当前任务
        self.state.current_task = None


# 兼容性函数
def create_main_agent(
    session_id: Optional[str] = None,
    config: Optional[Dict] = None,
    prompt_system_v2: Optional["PromptSystemV2"] = None,
    context_manager: Optional["ContextManager"] = None,
) -> MainAgent:
    """
    创建 MainAgent 实例的工厂函数

    Args:
        session_id: 会话 ID（可选）
        config: 配置字典（可选）
        prompt_system_v2: PromptSystemV2 实例（可选）
        context_manager: 上下文管理器实例（可选）

    Returns:
        MainAgent 实例
    """
    return MainAgent(
        session_id=session_id,
        config=config,
        prompt_system_v2=prompt_system_v2,
        context_manager=context_manager,
    )
