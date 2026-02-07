"""Agno-based Subagent infrastructure with task orchestration and lifecycle management."""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from nanobot.agent.task import Task, TaskStatus
from nanobot.agent.task_manager import TaskManager
from nanobot.agent.tools.filesystem import ListDirTool, ReadFileTool, WriteFileTool
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.agent.tools.shell import ExecTool
from nanobot.agent.tools.web import WebFetchTool, WebSearchTool
from nanobot.bus.events import InboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.monitor.progress_tracker import ProgressTracker
from nanobot.providers.base import LLMProvider


class AgnoSubagentConfig(BaseModel):
    """Configuration model for Agno Subagent."""

    max_iterations: int = Field(
        default=15, description="Maximum number of iterations per subagent task"
    )
    timeout: int = Field(default=300, description="Task timeout in seconds")
    model: Optional[str] = Field(default=None, description="LLM model to use for subagent")
    brave_api_key: Optional[str] = Field(default=None, description="Brave API key for web search")
    restrict_to_workspace: bool = Field(
        default=True, description="Restrict shell commands to workspace"
    )


class AgnoSubagent(BaseModel):
    """Data model representing an Agno Subagent instance."""

    subagent_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8], description="Unique subagent identifier"
    )
    task_id: str = Field(..., description="Associated task identifier")
    task: str = Field(..., description="Task description")
    label: str = Field(..., description="Human-readable task label")
    status: TaskStatus = Field(default=TaskStatus.RUNNING, description="Current task status")
    progress: float = Field(default=0.0, description="Task progress percentage (0-100)")
    iteration: int = Field(default=0, description="Current iteration count")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


class AgnoSubagentManager:
    """
    Agno-based Subagent Manager for advanced task execution with Human-in-loop support.

    This manager extends the base SubagentManager with enhanced features:
    - Risk assessment for high-risk operations
    - Message interruption mechanism
    - Session hooks for customization
    - Enhanced task orchestration
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
        self._subagent_map: Dict[str, AgnoSubagent] = {}  # subagent_id -> AgnoSubagent
        self._task_map: Dict[str, str] = {}  # task_id -> subagent_id
        self._progress_tracker = ProgressTracker(self._task_manager)
        self._risk_evaluator = None
        self._interrupt_handler = None
        self._hooks = None

    async def initialize(self):
        """Initialize the Agno Subagent Manager with required components."""
        from nanobot.agent.subagent.hooks import SubagentHooks
        from nanobot.agent.subagent.interrupt_handler import InterruptHandler
        from nanobot.agent.subagent.risk_evaluator import RiskEvaluator

        self._risk_evaluator = RiskEvaluator(self)
        self._interrupt_handler = InterruptHandler(self)
        self._hooks = SubagentHooks(self)

        logger.info("Agno Subagent Manager initialized successfully")

    async def spawn(
        self,
        task: str,
        label: str | None = None,
        origin_channel: str = "cli",
        origin_chat_id: str = "direct",
        session_key: str = "",
    ) -> str:
        """
        Spawn a new Agno Subagent to execute a task.

        Args:
            task: The task description for the subagent.
            label: Optional human-readable label for the task.
            origin_channel: The channel to announce results to.
            origin_chat_id: The chat ID to announce results to.
            session_key: Session key for context correlation.

        Returns:
            Subagent ID of the spawned subagent.
        """
        if self._risk_evaluator is None:
            await self.initialize()

        subagent_id = str(uuid.uuid4())[:8]
        display_label = label or task[:30] + ("..." if len(task) > 30 else "")

        # Create task record
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

        # Create AgnoSubagent instance
        agno_subagent = AgnoSubagent(
            subagent_id=subagent_id,
            task_id=task_id,
            task=task,
            label=display_label,
            status=TaskStatus.RUNNING,
        )
        self._subagent_map[subagent_id] = agno_subagent
        self._task_map[task_id] = subagent_id

        # Create background task
        bg_task = asyncio.create_task(
            self._run_subagent(
                subagent_id,
                task,
                display_label,
                {"channel": origin_channel, "chat_id": origin_chat_id},
                task_id,
            )
        )
        self._running_tasks[subagent_id] = bg_task

        # Cleanup when done
        bg_task.add_done_callback(lambda _: self._running_tasks.pop(subagent_id, None))

        logger.info(f"Agno Subagent [{subagent_id}] spawned for task: {display_label}")
        return subagent_id

    async def _run_subagent(
        self,
        subagent_id: str,
        task: str,
        label: str,
        origin: dict[str, str],
        task_id: str,
    ) -> None:
        """Execute the subagent task with enhanced orchestration."""
        logger.info(f"Agno Subagent [{subagent_id}] starting task: {label}")

        try:
            # Pre-run hook
            await self._hooks.pre_run(subagent_id)

            # Build subagent tools
            tools = await self._build_tools()

            # Build messages with Agno-specific prompt
            system_prompt = self._build_agno_prompt(task)
            messages: list[dict[str, Any]] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task},
            ]

            final_result: str | None = None
            for iteration in range(1, self.config.max_iterations + 1):
                # Update progress
                await self._update_subagent_progress(subagent_id, iteration, final_result)

                # Check for interruptions
                if await self._interrupt_handler.check_for_interrupt(subagent_id):
                    logger.warning(f"Agno Subagent [{subagent_id}] interrupted")
                    final_result = "Task execution was interrupted by user"
                    break

                response = await self.provider.chat(
                    messages=messages,
                    tools=tools.get_definitions(),
                    model=self.config.model or self.provider.get_default_model(),
                )

                if response.has_tool_calls:
                    # Evaluate tool call risks
                    if await self._risk_evaluator.evaluate_tool_calls(
                        subagent_id, response.tool_calls
                    ):
                        logger.info(f"Agno Subagent [{subagent_id}] executing tool calls")
                        await self._execute_tool_calls(
                            subagent_id, response.tool_calls, tools, messages
                        )
                    else:
                        logger.warning(
                            f"Agno Subagent [{subagent_id}] tool calls blocked due to high risk"
                        )
                        final_result = "Task execution was blocked due to high-risk operations requiring human approval"
                        break
                else:
                    final_result = response.content
                    break

            if final_result is None:
                final_result = "Task completed but no final response was generated."

            # Mark task as completed
            await self._complete_subagent(subagent_id, final_result, task_id)

            logger.info(f"Agno Subagent [{subagent_id}] completed successfully")
            await self._announce_result(subagent_id, label, task, final_result, origin, "ok")

        except asyncio.CancelledError:
            logger.info(f"Agno Subagent [{subagent_id}] was cancelled")
            final_result = "Task execution was cancelled"
            await self._cancel_subagent(subagent_id)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(f"Agno Subagent [{subagent_id}] failed: {e}")
            await self._fail_subagent(subagent_id, error_msg, task_id)
            await self._announce_result(subagent_id, label, task, error_msg, origin, "error")
        finally:
            # Post-run hook
            await self._hooks.post_run(subagent_id)

    async def _build_tools(self) -> ToolRegistry:
        """Build and register subagent tools."""
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
        """Execute tool calls and update message history."""
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
            logger.debug(f"Agno Subagent [{subagent_id}] executing: {tool_call.name}")
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
        """Update subagent progress and task status."""
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

    async def _complete_subagent(self, subagent_id: str, final_result: str, task_id: str):
        """Complete a subagent task."""
        if subagent_id not in self._subagent_map:
            return

        self._subagent_map[subagent_id].status = TaskStatus.COMPLETED
        self._subagent_map[subagent_id].progress = 100.0
        self._subagent_map[subagent_id].updated_at = datetime.now()

        task_obj = self._task_manager.get_task(task_id)
        if task_obj:
            task_obj.mark_completed(final_result)

    async def _cancel_subagent(self, subagent_id: str):
        """Cancel a running subagent."""
        if subagent_id not in self._subagent_map:
            return

        self._subagent_map[subagent_id].status = TaskStatus.CANCELLED
        self._subagent_map[subagent_id].updated_at = datetime.now()

        task_obj = self._task_manager.get_task(self._subagent_map[subagent_id].task_id)
        if task_obj:
            task_obj.status = TaskStatus.CANCELLED
            task_obj.updated_at = datetime.now()

    async def _fail_subagent(self, subagent_id: str, error_msg: str, task_id: str):
        """Mark a subagent task as failed."""
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
        """Announce the subagent result via the message bus."""
        status_text = "completed successfully" if status == "ok" else "failed"

        announce_content = f"""[Agno Subagent '{label}' {status_text}]

Task: {task}

Result:
{result}

Summarize this naturally for the user. Keep it brief (1-2 sentences). Do not mention technical details like "subagent" or task IDs."""

        msg = InboundMessage(
            channel="system",
            sender_id="agno_subagent",
            chat_id=f"{origin['channel']}:{origin['chat_id']}",
            content=announce_content,
        )

        await self.bus.publish_inbound(msg)
        logger.debug(
            f"Agno Subagent [{subagent_id}] announced result to {origin['channel']}:{origin['chat_id']}"
        )

    def _build_agno_prompt(self, task: str) -> str:
        """Build a focused system prompt for Agno Subagent."""
        return f"""# Agno Subagent

You are an Agno-based subagent spawned by the main agent to complete a specific task.
Agno provides advanced task orchestration and human-in-loop capabilities.

## Your Task
{task}

## Rules
1. Stay focused - complete only the assigned task, nothing else
2. Your final response will be reported back to the main agent
3. Do not initiate conversations or take on side tasks
4. Be concise but informative in your findings
5. High-risk operations will require human approval before execution

## What You Can Do
- Read and write files in the workspace
- Execute shell commands (with risk assessment)
- Search the web and fetch web pages
- Complete the task thoroughly

## What You Cannot Do
- Send messages directly to users (no message tool available)
- Spawn other subagents
- Access the main agent's conversation history
- Execute high-risk operations without approval

## Workspace
Your workspace is at: {self.workspace}

When you have completed the task, provide a clear summary of your findings or actions."""

    async def cancel_subagent(self, subagent_id: str) -> bool:
        """Cancel a running subagent."""
        if subagent_id in self._running_tasks:
            task = self._running_tasks[subagent_id]
            task.cancel()
            await self._cancel_subagent(subagent_id)
            logger.info(f"Agno Subagent [{subagent_id}] cancelled")
            return True
        return False

    def get_subagent_by_id(self, subagent_id: str) -> Optional[AgnoSubagent]:
        """Get subagent by ID."""
        return self._subagent_map.get(subagent_id)

    def get_subagent_by_task_id(self, task_id: str) -> Optional[AgnoSubagent]:
        """Get subagent by task ID."""
        subagent_id = self._task_map.get(task_id)
        if subagent_id:
            return self._subagent_map.get(subagent_id)
        return None

    def get_running_count(self) -> int:
        """Get number of running subagents."""
        return len([s for s in self._subagent_map.values() if s.status == TaskStatus.RUNNING])

    def get_all_subagents(self) -> List[AgnoSubagent]:
        """Get all subagent instances."""
        return list(self._subagent_map.values())

    def get_task_manager(self) -> TaskManager:
        """Get task manager instance."""
        return self._task_manager

    def get_progress_tracker(self) -> ProgressTracker:
        """Get progress tracker instance."""
        return self._progress_tracker
