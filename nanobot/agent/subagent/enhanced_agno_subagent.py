"""
Enhanced Agno Subagent - 增强版 Agno Subagent

改进点：
1. 在执行时通过 SkillLoader 动态加载技能详细内容
2. 将加载的技能内容作为系统提示的一部分
3. 支持根据 skills 字段配置执行环境
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from nanobot.agent.skill_loader import SkillLoader
from nanobot.agent.subagent.agno_subagent import (AgnoSubagent,
                                                  AgnoSubagentConfig)
from nanobot.agent.subagent.models import SubagentTask
from nanobot.agent.task import Task, TaskStatus
from nanobot.agent.task_manager import TaskManager
from nanobot.agent.tools.filesystem import (ListDirTool, ReadFileTool,
                                            WriteFileTool)
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.agent.tools.shell import ExecTool
from nanobot.agent.tools.web import WebFetchTool, WebSearchTool
from nanobot.bus.events import InboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.monitor.progress_tracker import ProgressTracker
from nanobot.providers.base import LLMProvider


class EnhancedAgnoSubagentManager:
    """
    增强版 Agno Subagent Manager

    改进功能：
    - Subagent 执行时通过 SkillLoader 动态加载技能详细内容
    - 将技能内容注入到系统提示中
    - 支持 skills 配置
    """

    def __init__(
        self,
        provider: LLMProvider,
        workspace: Path,
        bus: MessageBus,
        config: AgnoSubagentConfig = None,
    ):
        self.provider = provider
        self.workspace = workspace
        self.bus = bus
        self.config = config or AgnoSubagentConfig()
        self._running_tasks: dict[str, asyncio.Task[None]] = {}
        self._task_manager = TaskManager()
        self._subagent_map: Dict[str, AgnoSubagent] = {}
        self._task_map: Dict[str, str] = {}
        self._progress_tracker = ProgressTracker(self._task_manager)
        self._risk_evaluator = None
        self._interrupt_handler = None
        self._hooks = None

        # 🔥 新增：SkillLoader
        self.skill_loader = SkillLoader()
        logger.info("EnhancedAgnoSubagentManager: SkillLoader 已初始化")

    async def initialize(self):
        """初始化增强版 Agno Subagent Manager"""
        from nanobot.agent.subagent.hooks import SubagentHooks
        from nanobot.agent.subagent.interrupt_handler import InterruptHandler
        from nanobot.agent.subagent.risk_evaluator import RiskEvaluator

        self._risk_evaluator = RiskEvaluator(self)
        self._interrupt_handler = InterruptHandler(self)
        self._hooks = SubagentHooks(self)

        logger.info("EnhancedAgnoSubagentManager 初始化完成")

    async def spawn(
        self,
        task: str,
        label: str | None = None,
        origin_channel: str = "cli",
        origin_chat_id: str = "direct",
        session_key: str = "",
        skills: List[str] | None = None,
        agent_type: str = "agno",
        config: Dict[str, Any] | None = None,
    ) -> str:
        """
        创建新的 Agno Subagent（增强版）

        Args:
            task: 任务描述
            label: 任务标签
            origin_channel: 源渠道
            origin_chat_id: 源聊天 ID
            session_key: 会话 key
            skills: 技能列表（🔥 新增）
            agent_type: agent 类型
            config: 额外配置

        Returns:
            Subagent ID
        """
        if self._risk_evaluator is None:
            await self.initialize()

        subagent_id = str(uuid.uuid4())[:8]
        display_label = label or task[:30] + ("..." if len(task) > 30 else "")

        # 🔥 记录 skills 信息
        if skills:
            logger.info(f"EnhancedAgnoSubagentManager[{subagent_id}] 收到 skills: {skills}")

        # 创建任务记录
        task_obj = Task(
            type="agno_subagent",
            status=TaskStatus.RUNNING,
            original_message=task,
            current_task=task,
            progress=0.0,
            subagent_id=subagent_id,
            session_key=session_key,
            channel=origin_channel,
            chat_id=origin_chat_id,
        )
        task_id = self._task_manager.create_task(task_obj)

        # 创建 AgnoSubagent 实例
        agno_subagent = AgnoSubagent(
            subagent_id=subagent_id,
            task_id=task_id,
            task=task,
            label=display_label,
            status=TaskStatus.RUNNING,
        )
        self._subagent_map[subagent_id] = agno_subagent
        self._task_map[task_id] = subagent_id

        # 创建后台任务
        bg_task = asyncio.create_task(
            self._run_subagent(
                subagent_id,
                task {
                    "channel": origin_channel,
                    "chat_id": origin_chat_id,
                },
                task_id,
                skills=skills,  # 🔥 传递 skills
                agent_type=agent_type,
                config=config,
            )
        )
        self._running_tasks[subagent_id] = bg_task

        # 完成时清理
        bg_task.add_done_callback(lambda _: self._running_tasks.pop(subagent_id, None))

        logger.info(
            f"EnhancedAgnoSubagentManager[{subagent_id}] 已创建，"
            f"任务: {display_label}, skills={skills}"
        )
        return subagent_id

    async def _run_subagent(
        self,
        subagent_id: str,
        task: str,
        label: str,
        origin: dict[str, str],
        task_id: str,
        skills: List[str] | None = None,
        agent_type: str = "agno",
        config: Dict[str, Any] | None = None,
    ) -> None:
        """执行 subagent 任务（增强版）"""
        logger.info(
           "EnhancedAgnoSubagentManager[{subagent_id}] 开始执行任务: {label}, "
            f"skills={skills}, agent_type={agent_type}"
        )

        try:
            # Pre-run hook
            await self._hooks.pre_run(subagent_id)

            # 构建工具
            tools = await self._build_tools()

            # 🔥 动态加载技能详细内容
            skills_content = await self._load_skills_content(skills)

            # 🔥 构建增强的系统提示
            system_prompt = self._build_enhanced_agno_prompt(task, skills_content)
            messages: list[dict[str, Any]] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task},
            ]

            final_result: str | None = None
            for iteration in range(1, self.config.max_iterations + 1):
                # 更新进度
                await self._update_subagent_progress(subagent_id, iteration, final_result)

                # 检查中断
                if await self._interrupt_handler.check_for_interrupt(subagent_id):
                    logger.warning(f"EnhancedAgnoSubagentManager[{subagent_id}] 被中断")
                    final_result = "任务执行被用户中断"
                    break

                # 调用 LLM
                response = await self.provider.chat(
                    messages=messages,
                    tools=tools.get_definitions(),
                    model=self.config.model or self.provider.get_default_model(),
                )

                if response.has_tool_calls:
                    # 评估工具调用风险
                    if await self._risk_evaluator.evaluate_tool_calls(
                        subagent_id, response.tool_calls
                    ):
                        logger.info(f"EnhancedAgnoSubagentManager[{subagent_id}] 执行工具调用")
                        await self._execute_tool_calls(
                            subagent_id, response.tool_calls, tools, messages
                        )
                    else:
                        logger.warning(
                            f"EnhancedAgnoSubagentManager[{subagent_id}] "
                            "工具调用被风险阻止"
                        )
                        final_result = "任务执行因高风险操作需要人工批准而被阻止"
                        break
                else:
                    final_result = response.content
                    break

            if final_result is None:
                final_result = "任务已完成，但未生成最终响应。"

            # 标记任务完成
            await self._complete_subagent(subagent_id, final_result, task_id)

            logger.info(f"EnhancedAgnoSubagentManager[{subagent_id}] 成功完成")
            await self._announce_result(subagent_id, label, task, final_result, origin, "ok")

        except asyncio.CancelledError:
            logger.info(f"EnhancedAgnoSubagentManager[{subagent_id}] 被取消")
            final_result = "任务执行被取消"
            await self._cancel_subagent(subagent_id)
        except Exception as e:
            error_msg = f"错误: {str(e)}"
            logger.error(f"EnhancedAgnoSubagentManager[{subagent_id}] 失败: {e}")
            await self._fail_subagent(subagent_id, error_msg, task_id)
            await self._announce_result(subagent_id, label, task, error_msg, origin, "error")
        finally:
            # Post-run hook
            await self._hooks.post_run(subagent_id)

    async def _load_skills_content(self, skills: List[str] | None) -> Dict[str, str]:
        """
        🔥 动态加载技能详细内容

        Args:
            skills: 技能名称列表

        Returns:
            技能名称到内容的映射
        """
        skills_content = {}

        if not skills:
            logger.debug("EnhancedAgnoSubagentManager: 未提供 skills，跳过加载")
            return skills_content

        for skill_name in skills:
            try:
                content = await self.skill_loader.load_skill_content(skill_name)
                if content:
                    skills_content[skill_name] = content
                    logger.debug(
                        f"EnhancedAgnoSubagentManager: 技能 '{skill_name}' 内容加载成功"
                    )
                else:
                    logger.warning(
                        f"EnhancedAgnoSubagentManager: 技能 '{skill_name}' 内容未找到"
                    )
            except Exception as e:
                logger.error(
                    f"EnhancedAgnoSubagentManager: 加载技能 '{skill_name}' 失败: {e}"
                )

        return skills_content

    def _build_enhanced_agno_prompt(
        self, task: str, skills_content: Dict[str, str]
    ) -> str:
        """
        🔥 构建增强的系统提示（包含技能内容）

        Args:
            task: 任务描述
            skills_content: 技能内容映射

        Returns:
            系统提示
        """
        base_prompt = f"""# Enhanced Agno Subagent

You are an enhanced Agno-based subagent spawned by the main agent to complete a specific task.

## Your Task
{task}

## Available Skills
"""

        if skills_content:
            for skill_name, content in skills_content.items():
                base_prompt += f"\n### {skill_name}\n{content}\n"
        else:
            base_prompt += "\nNo specific skills loaded. You can use your general capabilities.\n"

        base_prompt += f"""
## Rules
1. Stay focused - complete only the assigned task, nothing else
2. Your final response will be reported back to the main agent
3. Do not initiate conversations or take on side tasks
4. Be concise but informative in your findings
5. High-risk operations will require human approval before execution

## What You Can Do
- Read and write files in the workspace
- Execute shell commands (with risk assessment)
- Search web and fetch web pages
- Complete the task thoroughly

## What You Cannot Do
- Send messages directly to users (no message tool available)
- Spawn other subagents
- Access the main agent's conversation history
- Execute high-risk operations without approval

## Workspace
Your workspace is at: {self.workspace}

When you have completed the task, provide a clear summary of your findings or actions.
"""

        return base_prompt

    async def _build_tools(self) -> ToolRegistry:
        """构建和注册 subagent 工具"""
        tools = ToolRegistry()
        tools.register(ReadFileTool())
        tools.register(WriteFileTool())
        tools.register(ListDirTool())
        tools.register(
            ExecTool(
                working_dir=str(self.workspace),
                timeout=self.config.timeout,
                restrict_to_workspace=self.config.restrict_to_workspace,
            )
        )
        tools.register(WebSearchTool(api_key=self.config.brave_api_key))
        tools.register(WebFetchTool())

        # Hook for custom tool registration
        await self._hooks.register_tools(tools)
        return tools

    async def _execute_tool_calls(
        self,
        subagent_id: str,
        tool_calls: List[Any],
        tools: ToolRegistry,
        messages: List[Dict[str, Any]],
    ):
        """执行工具调用并更新消息历史"""
        tool_call_dicts = []
        for tc in tool_calls:
            tool_call_dicts.append(
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": tc.arguments,
                    },
                }
            )

        messages.append(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": tool_call_dicts,
            }
        )

        for tool_call in tool_calls:
            logger.debug(f"EnhancedAgnoSubagentManager[{subagent_id}] 执行: {tool_call.name}")
            result = await tools.execute(tool_call.name, tool_call.arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.name,
                    "content": result,
                }
            )

    async def _update_subagent_progress(
        self, subagent_id: str, iteration: int, final_result: Optional[str] = None
    ):
        """更新 subagent 进度和任务状态"""
        if subagent_id not in self._subagent_map:
            return

        progress = (iteration / self.config.max_iterations) * 100
        self._subagent_map[subagent_id].iteration = iteration
        self._subagent_map[subagent_id].progress = progress
        self._subagent_map[subagent_id].updated_at = datetime.now()

        self._task_manager.update_task(
            self._subagent_map[subagent_id].task_id,
            {"progress": progress, "updated_at": datetime.now()},
        )

        self._progress_tracker.track_progress(
            self._subagent_map[subagent_id].task_id,
            progress,
            f"Iteration {iteration}/{self.config.max_iterations}",
        )

    async def _rsubagent(self, subagent_id: str, final_result: str, task_id: str):
        """完成 subagent 任务"""
        if subagent_id not in self._subagent_map:
            return

        self._subagent_map[subagent_id].status = TaskStatus.COMPLETED
        self._subagent_map[subagent_id].progress = 100.0
        self._subagent_map[subagent_id].updated_at = datetime.now()

        task_obj = self._task_manager.get_task(task_id)
        if task_obj:
            task_obj.mark_completed(final_result)

    async def _cancel_subagent(self, subagent_id: str):
        """取消正在运行的 subagent"""
        if subagent_id not in self._subagent_map:
            return

        self._subagent_map[subagent_id].status = TaskStatus.CANCELLED
        self._subagent_map[subagent_id].updated_at = datetime.now()

        task_obj = self._task_manager.get_task(self._subagent_map[subagent_id].task_id)
        if task_obj:
            task_obj.status = TaskStatus.CANCELLED
            task_obj.updated_at = datetime.now()

    async def _fail_subagent(self, subagent_id: str, error_msg: str, task_id: str):
        """标记 subagent 任务为失败"""
        if subagent_id not in self._subagent_map:
            return

        self._subagent_map[subagent_id].status = TaskStatus.FAILED
        self._subagent_map[subagent_id].updated_at = datetime.now()

        task_obj = self._task_manager.get_task(task_id)
        if task_obj:
            task_obj.mark_failed(error_msg)

    async def _announce_result(
        self,
        subagent_id: str,
        label: str,
        task: str,
        result: str,
        origin: dict[str, str],
        status: str,
    ):
        """通过消息总线宣布 subagent 结果"""
        status_text = "成功完成" if status == "ok" else "失败"

        announce_content = f"""[Agno Subagent '{label}' {status_text}]

任务: {task}

结果:
{result}

请自然地总结给用户。保持简洁（1-2 句话）。不要提及技术细节如 "subagent" 或任务 ID。"""

        msg = InboundMessage(
            channel="system",
            sender_id="enhanced_agno_subagent",
            chat_id=f"{origin['channel']}:{origin['chat_id']}",
            content=announce_content,
        )

        await self.bus.publish_inbound(msg)
        logger.debug(
            f"EnhancedAgnoSubagentManager[{subagent_id}] "
            f"结果已宣布到 {origin['channel']}:{origin['chat_id']}"
        )

    async def cancel_subagent(self, subagent_id: str) -> bool:
        """取消正在运行的子代理"""
        if subagent_id in self._running_tasks:
            task = self._running_tasks[subagent_id]
            task.cancel()
            await self._cancel_subagent(subagent_id)
            logger.info(f"EnhancedAgnoSubagentManager[{subagent_id}] 已取消")
            return True
        return False

    def get_subagent_by_id(self, subagent_id: str) -> Optional[AgnoSubagent]:
        """通过 ID 获取 subagent"""
        return self._subagent_map.get(subagent_id)

    def get_subagent_by_task_id(self, task_id: str) -> Optional[AgnoSubagent]:
        """通过任务 ID 获取 subagent"""
        subagent_id = self._task_map.get(task_id)
        if subagent_id:
            return self._subagent_map.get(subagent_id)
        return None

    def get_running_count(self) -> int:
        """获取正在运行的子代理数量"""
        return len([s for s in self._subagent_map.values() if s.status == TaskStatus.RUNNING])

    def get_all_subagents(self) -> List[AgnoSubagent]:
        """获取所有子代理实例"""
        return list(self._subagent_map.values())

    def get_task_manager(self) -> TaskManager:
        """获取任务管理器实例"""
        return self._task_manager

    def get_progress_tracker(self) -> ProgressTracker:
        """获取进度追踪器实例"""
        return self._progress_tracker
