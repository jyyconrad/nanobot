"""Base Subagent manager for background task execution with task tracking and correction support."""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

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


class SubagentManager:
    """
    Manages background subagent execution with task tracking and correction support.

    Subagents are lightweight agent instances that run in the background
    to handle specific tasks. They share the same LLM provider but have
    isolated context and a focused system prompt.
    """

    def __init__(
        self,
        provider: LLMProvider,
        workspace: Path,
        bus: MessageBus,
        model: str | None = None,
        brave_api_key: str | None = None,
        exec_config: Optional[Any] = None,
    ):
        from nanobot.config.schema import ExecToolConfig

        self.provider = provider
        self.workspace = workspace
        self.bus = bus
        self.model = model or provider.get_default_model()
        self.brave_api_key = brave_api_key
        self.exec_config = exec_config or ExecToolConfig()
        self._running_tasks: dict[str, asyncio.Task[None]] = {}
        self._task_manager = TaskManager()
        self._task_map: Dict[str, str] = {}  # subagent_id -> task_id
        self._progress_tracker = ProgressTracker(self._task_manager)

    async def spawn(
        self,
        task: str,
        label: str | None = None,
        origin_channel: str = "cli",
        origin_chat_id: str = "direct",
        session_key: str = "",
    ) -> str:
        """
        Spawn a subagent to execute a task in the background.

        Args:
            task: The task description for the subagent.
            label: Optional human-readable label for the task.
            origin_channel: The channel to announce results to.
            origin_chat_id: The chat ID to announce results to.
            session_key: Session key for context correlation.

        Returns:
            Status message indicating the subagent was started.
        """
        subagent_id = str(uuid.uuid4())[:8]
        display_label = label or task[:30] + ("..." if len(task) > 30 else "")

        origin = {
            "channel": origin_channel,
            "chat_id": origin_chat_id,
        }

        # Create task record
        task_obj = Task(
            type="subagent",
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
        self._task_map[subagent_id] = task_id

        # Create background task
        bg_task = asyncio.create_task(
            self._run_subagent(subagent_id, task, display_label, origin, task_id)
        )
        self._running_tasks[subagent_id] = bg_task

        # Cleanup when done
        bg_task.add_done_callback(lambda _: self._running_tasks.pop(subagent_id, None))

        logger.info(f"Spawned subagent [{subagent_id}]: {display_label}")
        return f"Subagent [{display_label}] started (id: {subagent_id}). I'll notify you when it completes."

    async def _run_subagent(
        self,
        subagent_id: str,
        task: str,
        label: str,
        origin: dict[str, str],
        task_id: str,
    ) -> None:
        """Execute the subagent task, track progress, and announce the result."""
        logger.info(f"Subagent [{subagent_id}] starting task: {label}")

        try:
            # Build subagent tools (no message tool, no spawn tool)
            tools = ToolRegistry()
            tools.register(ReadFileTool())
            tools.register(WriteFileTool())
            tools.register(ListDirTool())
            tools.register(
                ExecTool(
                    working_dir=str(self.workspace),
                    timeout=self.exec_config.timeout,
                    restrict_to_workspace=self.exec_config.restrict_to_workspace,
                )
            )
            tools.register(WebSearchTool(api_key=self.brave_api_key))
            tools.register(WebFetchTool())

            # Build messages with subagent-specific prompt
            system_prompt = self._build_subagent_prompt(task)
            messages: list[dict[str, Any]] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task},
            ]

            # Run agent loop (limited iterations)
            max_iterations = 15
            iteration = 0
            final_result: str | None = None

            while iteration < max_iterations:
                iteration += 1

                # Update progress
                progress = (iteration / max_iterations) * 100
                self._task_manager.update_task(
                    task_id, {"progress": progress, "updated_at": datetime.now()}
                )

                # Track progress
                self._progress_tracker.track_progress(
                    task_id, progress, f"Iteration {iteration}/{max_iterations}"
                )

                response = await self.provider.chat(
                    messages=messages,
                    tools=tools.get_definitions(),
                    model=self.model,
                )

                if response.has_tool_calls:
                    # Add assistant message with tool calls
                    tool_call_dicts = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            },
                        }
                        for tc in response.tool_calls
                    ]
                    messages.append(
                        {
                            "role": "assistant",
                            "content": response.content or "",
                            "tool_calls": tool_call_dicts,
                        }
                    )

                    # Execute tools
                    for tool_call in response.tool_calls:
                        logger.debug(f"Subagent [{subagent_id}] executing: {tool_call.name}")
                        result = await tools.execute(tool_call.name, tool_call.arguments)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.name,
                                "content": result,
                            }
                        )
                else:
                    final_result = response.content
                    break

            if final_result is None:
                final_result = "Task completed but no final response was generated."

            logger.info(f"Subagent [{subagent_id}] completed successfully")

            # Mark task as completed
            task_obj = self._task_manager.get_task(task_id)
            if task_obj:
                task_obj.mark_completed(final_result)

            await self._announce_result(subagent_id, label, task, final_result, origin, "ok")

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(f"Subagent [{subagent_id}] failed: {e}")

            # Mark task as failed
            task_obj = self._task_manager.get_task(task_id)
            if task_obj:
                task_obj.mark_failed(error_msg)

            await self._announce_result(subagent_id, label, task, error_msg, origin, "error")

    async def _announce_result(
        self,
        task_id: str,
        label: str,
        task: str,
        result: str,
        origin: dict[str, str],
        status: str,
    ) -> None:
        """Announce the subagent result to the main agent via the message bus."""
        status_text = "completed successfully" if status == "ok" else "failed"

        announce_content = f"""[Subagent '{label}' {status_text}]

Task: {task}

Result:
{result}

Summarize this naturally for the user. Keep it brief (1-2 sentences). Do not mention technical details like "subagent" or task IDs."""

        # Inject as system message to trigger main agent
        msg = InboundMessage(
            channel="system",
            sender_id="subagent",
            chat_id=f"{origin['channel']}:{origin['chat_id']}",
            content=announce_content,
        )

        await self.bus.publish_inbound(msg)
        logger.debug(
            f"Subagent [{task_id}] announced result to {origin['channel']}:{origin['chat_id']}"
        )

    def _build_subagent_prompt(self, task: str) -> str:
        """Build a focused system prompt for the subagent using PromptBuilder."""
        from nanobot.agent.prompt_builder import get_prompt_builder

        return get_prompt_builder().build_subagent_prompt(
            task_description=task,
            workspace=self.workspace,
            available_tools=ToolRegistry(),
        )

    def get_running_count(self) -> int:
        """Return the number of currently running subagents."""
        return len(self._running_tasks)

    def get_task_manager(self) -> TaskManager:
        """Get the task manager instance."""
        return self._task_manager

    def get_progress_tracker(self) -> ProgressTracker:
        """Get the progress tracker instance."""
        return self._progress_tracker

    def get_task_by_subagent_id(self, subagent_id: str) -> Optional[Task]:
        """Get task by subagent ID."""
        task_id = self._task_map.get(subagent_id)
        if task_id:
            return self._task_manager.get_task(task_id)
        return None

    def get_subagent_by_task_id(self, task_id: str) -> Optional[str]:
        """Get subagent ID by task ID."""
        for subagent_id, tid in self._task_map.items():
            if tid == task_id:
                return subagent_id
        return None

    def get_task_map(self) -> Dict[str, str]:
        """Get the subagent to task mapping."""
        return self._task_map.copy()

    def get_all_subagent_ids(self) -> List[str]:
        """Get all active subagent IDs."""
        return list(self._running_tasks.keys())

    async def cancel_subagent(self, subagent_id: str) -> bool:
        """Cancel a running subagent."""
        if subagent_id in self._running_tasks:
            task = self._running_tasks[subagent_id]
            task.cancel()

            # Update task status
            task_obj = self.get_task_by_subagent_id(subagent_id)
            if task_obj:
                task_obj.status = TaskStatus.CANCELLED
                task_obj.updated_at = datetime.now()

            logger.info(f"Subagent [{subagent_id}] cancelled")
            return True
        return False

    async def update_task_progress(self, task_id: str, progress: float, message: str = ""):
        """Update task progress."""
        task = self._task_manager.get_task(task_id)
        if task:
            task.update_progress(progress, message)

    async def correct_task(self, task_id: str, new_task: str) -> Optional[str]:
        """
        Correct an existing task by spawning a new subagent with updated task description.

        Args:
            task_id: Original task ID to correct
            new_task: New task description

        Returns:
            New subagent ID if created successfully
        """
        original_task = self._task_manager.get_task(task_id)
        if not original_task:
            logger.warning(f"Task {task_id} not found")
            return None

        # Cancel original subagent if running
        subagent_id = self.get_subagent_by_task_id(task_id)
        if subagent_id:
            await self.cancel_subagent(subagent_id)

        # Spawn new subagent with corrected task
        new_subagent = await self.spawn(
            task=new_task,
            label=f"Correction: {original_task.current_task[:25]}...",
            origin_channel=original_task.channel,
            origin_chat_id=original_task.chat_id,
            session_key=original_task.session_key,
        )

        # Update original task as cancelled and create new task record
        original_task.status = TaskStatus.CANCELLED
        original_task.updated_at = datetime.now()

        logger.info(f"Task {task_id} corrected, new subagent: {new_subagent}")
        return new_subagent
