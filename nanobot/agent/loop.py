"""Agent loop: the core processing engine."""

import asyncio
import datetime
import json
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from nanobot.agent.context import ContextBuilder
from nanobot.agent.context_monitor import ContextMonitor, ContextMonitorConfig
from nanobot.agent.main_agent import MainAgent
from nanobot.agent.subagent import SubagentManager
from nanobot.agent.task import TaskStatus
from nanobot.agent.tools.message import MessageTool
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.agent.tools.shell import ExecTool
from nanobot.agent.tools.spawn import SpawnTool
from nanobot.agent.tools.web import WebFetchTool, WebSearchTool
from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.agent.tools.filesystem import ReadFileTool, WriteFileTool, ListDirTool
from nanobot.commands.registry import CommandRegistry
from nanobot.config.schema import ExecToolConfig
from nanobot.providers.base import LLMProvider
from nanobot.session.manager import SessionManager


class AgentLoop:
    """
    The agent loop is the core processing engine.

    It:
    1. Receives messages from the bus
    2. Builds context with history, memory, skills
    3. Calls the LLM
    4. Executes tool calls
    5. Sends responses back
    """

    def __init__(
        self,
        bus: MessageBus,
        provider: LLMProvider,
        workspace: Path,
        model: str | None = None,
        max_iterations: int = 20,
        brave_api_key: str | None = None,
        exec_config: "ExecToolConfig | None" = None,
        opencode_config: dict | None = None,
    ):
        self.bus = bus
        self.provider = provider
        self.workspace = workspace
        self.model = model or provider.get_default_model()
        self.max_iterations = max_iterations
        self.brave_api_key = brave_api_key
        self.exec_config = exec_config or ExecToolConfig()

        self.context = ContextBuilder(workspace, opencode_config=opencode_config)
        self.sessions = SessionManager(workspace)
        self.tools = ToolRegistry()
        self.subagents = SubagentManager(
            provider=provider,
            workspace=workspace,
            bus=bus,
            model=self.model,
            brave_api_key=brave_api_key,
            exec_config=self.exec_config,
        )

        # 初始化 ContextMonitor 用于上下文管理
        self.context_monitor = ContextMonitor(ContextMonitorConfig(
            model=self.model,
            threshold=0.8,  # 默认 80% 阈值
            enable_auto_compression=True,
            compression_strategy="intelligent",
        ))

        # 添加命令系统
        self.commands = CommandRegistry()

        # 初始化 MainAgent 实例池
        self.main_agents: dict[str, MainAgent] = {}

        self._running = False
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register the default set of tools."""
        # File tools
        self.tools.register(ReadFileTool())
        self.tools.register(WriteFileTool())
        self.tools.register(ListDirTool())

        # Shell tool
        self.tools.register(
            ExecTool(
                working_dir=str(self.workspace),
                timeout=self.exec_config.timeout,
                restrict_to_workspace=self.exec_config.restrict_to_workspace,
            )
        )

        # Web tools
        self.tools.register(WebSearchTool(api_key=self.brave_api_key))
        self.tools.register(WebFetchTool())

        # Message tool
        message_tool = MessageTool(send_callback=self.bus.publish_outbound)
        self.tools.register(message_tool)

        # Spawn tool (for subagents)
        spawn_tool = SpawnTool(manager=self.subagents)
        self.tools.register(spawn_tool)

        # MCP tool
        from nanobot.agent.tools.mcp import MCPTool

        # Load MCP server configurations from config
        mcp_config = []
        if hasattr(self, "opencode_config") and self.opencode_config:
            mcp_servers = self.opencode_config.get("mcp_servers", [])
            for server in mcp_servers:
                mcp_config.append(
                    {
                        "server_url": server.get("url"),
                        "server_name": server.get("name"),
                        "auth_token": server.get("auth_token"),
                        "auth_type": server.get("auth_type", "bearer"),
                    }
                )

        # Register MCP tool
        self.tools.register(MCPTool(config=mcp_config))

    async def run(self) -> None:
        """Run the agent loop, processing messages from the bus."""
        self._running = True
        logger.info("Agent loop started")

        while self._running:
            try:
                # Wait for next message
                msg = await asyncio.wait_for(self.bus.consume_inbound(), timeout=1.0)

                # Process it
                try:
                    response = await self._process_message(msg)
                    if response:
                        await self.bus.publish_outbound(response)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Send error response
                    await self.bus.publish_outbound(
                        OutboundMessage(
                            channel=msg.channel,
                            chat_id=msg.chat_id,
                            content=f"Sorry, I encountered an error: {str(e)}",
                        )
                    )
            except asyncio.TimeoutError:
                continue

    def stop(self) -> None:
        """Stop the agent loop."""
        self._running = False
        logger.info("Agent loop stopping")

    async def _process_message(self, msg: InboundMessage) -> OutboundMessage | None:
        """
        Process a single inbound message with intelligent task routing.

        Args:
            msg: The inbound message to process.

        Returns:
            The response message, or None if no response needed.
        """
        # Handle system messages (subagent announces)
        # The chat_id contains the original "channel:chat_id" to route back to
        if msg.channel == "system":
            return await self._process_system_message(msg)

        logger.info(f"Processing message from {msg.channel}:{msg.sender_id}")

        # 检查命令
        command_name, args = self.commands.parse_command(msg.content)
        if command_name:
            return await self._handle_command(msg, command_name, args)

        # 获取或创建 MainAgent 实例
        if msg.session_key not in self.main_agents:
            logger.debug(f"Creating new MainAgent for session: {msg.session_key}")
            self.main_agents[msg.session_key] = MainAgent(msg.session_key, agent_loop=self)

        main_agent = self.main_agents[msg.session_key]

        # 使用 MainAgent 处理消息
        try:
            # 获取会话历史并监控上下文大小
            session = self.sessions.get_or_create(msg.session_key)
            history = session.get_history()

            # 监控上下文大小并自动压缩
            if self.context_monitor.check_threshold(history):
                logger.info("上下文大小接近阈值，将自动压缩")
                compressed_history = await self.context_monitor.compress_context(history)
                logger.debug(f"上下文压缩完成，原始消息数: {len(history)}, 压缩后: {len(compressed_history)}")

            # 处理消息
            response_content = await main_agent.process_message(msg.content)

            # 保存到会话历史
            session.add_message("user", msg.content)
            session.add_message("assistant", response_content)
            self.sessions.save(session)

            return OutboundMessage(
                channel=msg.channel, chat_id=msg.chat_id, content=response_content
            )

        except Exception as e:
            logger.error(f"MainAgent processing failed: {e}", exc_info=True)
            return OutboundMessage(
                channel=msg.channel, chat_id=msg.chat_id, content=f"处理消息时发生错误: {str(e)}"
            )

    async def _handle_command(self, msg: InboundMessage, command_name: str, args: dict[str, Any]) -> OutboundMessage:
        """处理命令执行"""
        command = self.commands.get(command_name)
        if not command:
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=f"Unknown command: /{command_name}",
            )

        try:
            context = {
                "args": args,
                "workspace": self.workspace,
                "provider": self.provider,
                "model": self.model,
                "skills": self.context.skills,
                "session": self.sessions.get_or_create(msg.session_key),
            }

            result = await command.execute(context)

            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=result,
            )
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=f"Error: {str(e)}",
            )

    async def _process_system_message(self, msg: InboundMessage) -> OutboundMessage | None:
        """
        Process a system message (e.g., subagent announce).

        The chat_id field contains "original_channel:original_chat_id" to route
        the response back to the correct destination.
        """
        logger.info(f"Processing system message from {msg.sender_id}")

        # Parse origin from chat_id (format: "channel:chat_id")
        if ":" in msg.chat_id:
            parts = msg.chat_id.split(":", 1)
            origin_channel = parts[0]
            origin_chat_id = parts[1]
        else:
            # Fallback
            origin_channel = "cli"
            origin_chat_id = msg.chat_id

        # Use the origin session for context
        session_key = f"{origin_channel}:{origin_chat_id}"
        session = self.sessions.get_or_create(session_key)

        # Update tool contexts
        message_tool = self.tools.get("message")
        if isinstance(message_tool, MessageTool):
            message_tool.set_context(origin_channel, origin_chat_id)

        spawn_tool = self.tools.get("spawn")
        if isinstance(spawn_tool, SpawnTool):
            spawn_tool.set_context(origin_channel, origin_chat_id)

        # Build messages with the announce content, using context monitor for size management
        history = session.get_history()
        if self.context_monitor.check_threshold(history):
            logger.info("系统消息处理时上下文大小接近阈值，将自动压缩")
            compressed_history = await self.context_monitor.compress_context(history)
            logger.debug(f"上下文压缩完成，原始消息数: {len(history)}, 压缩后: {len(compressed_history)}")
            history = compressed_history

        messages = self.context.build_messages(
            history=history, current_message=msg.content
        )

        # Agent loop (limited for announce handling)
        iteration = 0
        final_content = None

        while iteration < self.max_iterations:
            iteration += 1

            response = await self.provider.chat(
                messages=messages, tools=self.tools.get_definitions(), model=self.model
            )

            if response.has_tool_calls:
                tool_call_dicts = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                    }
                    for tc in response.tool_calls
                ]
                messages = self.context.add_assistant_message(
                    messages, response.content, tool_call_dicts
                )

                for tool_call in response.tool_calls:
                    args_str = json.dumps(tool_call.arguments)
                    logger.debug(f"Executing tool: {tool_call.name} with arguments: {args_str}")
                    result = await self.tools.execute(tool_call.name, tool_call.arguments)
                    messages = self.context.add_tool_result(
                        messages, tool_call.id, tool_call.name, result
                    )
            else:
                final_content = response.content
                break

        if final_content is None:
            final_content = "Background task completed."

        # Save to session (mark as system message in history)
        session.add_message("user", f"[System: {msg.sender_id}] {msg.content}")
        session.add_message("assistant", final_content)
        self.sessions.save(session)

        return OutboundMessage(
            channel=origin_channel, chat_id=origin_chat_id, content=final_content
        )

    async def _handle_task_correction(
        self, msg: InboundMessage, task_id: str, reason: str
    ) -> Optional[OutboundMessage]:
        """
        Handle task correction by creating a new subagent with updated task description.

        Args:
            msg: Original message
            task_id: Task ID to correct
            reason: Analysis reason

        Returns:
            Response message
        """
        task = self.bus.get_task_manager().get_task(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for correction")
            return None

        logger.info(f"Correcting task {task_id}: {reason}")

        # Create a correction task
        correction_msg = f"修正任务：{task.current_task} - 新要求：{msg.content}"

        # Spawn new subagent
        subagent_msg = await self.subagents.correct_task(task_id, correction_msg)

        return OutboundMessage(
            channel=msg.channel,
            chat_id=msg.chat_id,
            content=subagent_msg or f"任务 {task_id} 修正失败",
        )

    async def _handle_task_cancellation(
        self, msg: InboundMessage, task_id: str, reason: str
    ) -> Optional[OutboundMessage]:
        """
        Handle task cancellation.

        Args:
            msg: Original message
            task_id: Task ID to cancel
            reason: Analysis reason

        Returns:
            Response message
        """
        task = self.bus.get_task_manager().get_task(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for cancellation")
            return None

        logger.info(f"Cancelling task {task_id}: {reason}")

        # Cancel the subagent if it's running
        subagent_id = self.subagents.get_subagent_by_task_id(task_id)
        if subagent_id:
            await self.subagents.cancel_subagent(subagent_id)

        # Update task status
        task.status = TaskStatus.CANCELLED
        task.updated_at = datetime.datetime.now()

        return OutboundMessage(
            channel=msg.channel, chat_id=msg.chat_id, content=f"任务 '{task.current_task}' 已取消"
        )

    async def process_direct(self, content: str, session_key: str = "cli:direct") -> str:
        """
        Process a message directly (for CLI usage).

        Args:
            content: The message content.
            session_key: Session identifier.

        Returns:
            The agent's response.
        """
        msg = InboundMessage(channel="cli", sender_id="user", chat_id="direct", content=content)

        response = await self._process_message(msg)
        return response.content if response else ""
