"""Message interruption mechanism for Human-in-loop interaction with subagents."""

import asyncio
from datetime import datetime
from typing import Dict, Optional, Set

from loguru import logger
from pydantic import BaseModel, Field

from nanobot.agent.subagent.agno_subagent import AgnoSubagentManager
from nanobot.bus.events import InboundMessage
from nanobot.bus.queue import MessageBus


class InterruptType(BaseModel):
    """Interrupt type classification model."""

    type: str = Field(..., description="Interrupt type: cancel, correct, pause, resume")
    priority: int = Field(..., description="Interrupt priority (1-5)")
    description: str = Field(..., description="Interrupt description")


class InterruptRequest(BaseModel):
    """Interrupt request model."""

    request_id: str = Field(..., description="Unique interrupt request identifier")
    subagent_id: str = Field(..., description="Target subagent ID")
    type: str = Field(..., description="Interrupt type")
    message: str = Field(..., description="Interrupt message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Request timestamp")
    processed: bool = Field(default=False, description="Whether the interrupt has been processed")


class InterruptHandler:
    """
    Message interruption mechanism for Human-in-loop interaction.

    This component handles interrupt requests from users and implements
    cancel, correct, pause, and resume functionality for running subagents.
    """

    def __init__(self, manager: AgnoSubagentManager):
        self.manager = manager
        self.bus: MessageBus = manager.bus
        self._pending_interrupts: Dict[str, InterruptRequest] = {}
        self._paused_subagents: Set[str] = set()
        self._interrupt_types = {
            "cancel": InterruptType(type="cancel", priority=5, description="Cancel task immediately"),
            "correct": InterruptType(type="correct", priority=4, description="Correct task description"),
            "pause": InterruptType(type="pause", priority=3, description="Pause task execution"),
            "resume": InterruptType(type="resume", priority=2, description="Resume paused task"),
            "status": InterruptType(type="status", priority=1, description="Check task status")
        }

    async def check_for_interrupt(self, subagent_id: str) -> bool:
        """
        Check if there are any pending interrupt requests for the subagent.

        Args:
            subagent_id: Subagent ID to check

        Returns:
            True if interrupt was processed, False otherwise
        """
        if subagent_id not in self._pending_interrupts:
            return False

        interrupt = self._pending_interrupts.pop(subagent_id)
        interrupt.processed = True

        await self._handle_interrupt(subagent_id, interrupt)
        return True

    async def _handle_interrupt(self, subagent_id: str, interrupt: InterruptRequest):
        """Handle a specific interrupt request."""
        logger.info(f"Handling interrupt {interrupt.type} for subagent [{subagent_id}]")

        handler = self._get_interrupt_handler(interrupt.type)
        if handler:
            await handler(subagent_id, interrupt)
        else:
            logger.warning(f"Unknown interrupt type: {interrupt.type}")

    def _get_interrupt_handler(self, interrupt_type: str):
        """Get the appropriate handler for an interrupt type."""
        handlers = {
            "cancel": self._handle_cancel,
            "correct": self._handle_correct,
            "pause": self._handle_pause,
            "resume": self._handle_resume,
            "status": self._handle_status
        }
        return handlers.get(interrupt_type)

    async def _handle_cancel(self, subagent_id: str, interrupt: InterruptRequest):
        """Handle cancel interrupt."""
        await self.manager.cancel_subagent(subagent_id)
        logger.info(f"Subagent [{subagent_id}] cancelled via interrupt")

    async def _handle_correct(self, subagent_id: str, interrupt: InterruptRequest):
        """Handle correct interrupt."""
        subagent = self.manager.get_subagent_by_id(subagent_id)
        if not subagent:
            logger.warning(f"Subagent [{subagent_id}] not found")
            return

        logger.info(f"Correcting subagent [{subagent_id}] with new task: {interrupt.message}")
        await self.manager.cancel_subagent(subagent_id)

        # Spawn new subagent with corrected task
        new_subagent_id = await self.manager.spawn(
            task=interrupt.message,
            label=f"Correction: {subagent.label}",
            origin_channel="system",
            origin_chat_id="direct",
            session_key=""
        )

        logger.info(f"Subagent [{subagent_id}] corrected to [{new_subagent_id}]")

    async def _handle_pause(self, subagent_id: str, interrupt: InterruptRequest):
        """Handle pause interrupt."""
        self._paused_subagents.add(subagent_id)
        logger.info(f"Subagent [{subagent_id}] paused via interrupt")

    async def _handle_resume(self, subagent_id: str, interrupt: InterruptRequest):
        """Handle resume interrupt."""
        self._paused_subagents.remove(subagent_id)
        logger.info(f"Subagent [{subagent_id}] resumed via interrupt")

    async def _handle_status(self, subagent_id: str, interrupt: InterruptRequest):
        """Handle status check interrupt."""
        subagent = self.manager.get_subagent_by_id(subagent_id)
        if subagent:
            status_content = f"""Subagent [{subagent_id}] Status:
- Task: {subagent.task}
- Label: {subagent.label}
- Status: {subagent.status}
- Progress: {subagent.progress:.1f}%
- Iteration: {subagent.iteration}
- Created: {subagent.created_at}
- Updated: {subagent.updated_at}
"""
            msg = InboundMessage(
                channel="system",
                sender_id="interrupt_handler",
                chat_id="direct",
                content=status_content,
            )
            await self.bus.publish_inbound(msg)
            logger.debug(f"Status report sent for subagent [{subagent_id}]")
        else:
            logger.warning(f"Subagent [{subagent_id}] not found")

    async def add_interrupt(self, subagent_id: str, interrupt_type: str, message: str = ""):
        """
        Add a new interrupt request.

        Args:
            subagent_id: Target subagent ID
            interrupt_type: Type of interrupt
            message: Additional message

        Returns:
            Interrupt request object
        """
        if interrupt_type not in self._interrupt_types:
            logger.warning(f"Unknown interrupt type: {interrupt_type}")
            return None

        request = InterruptRequest(
            request_id=f"intr_{subagent_id}_{datetime.now().timestamp()}",
            subagent_id=subagent_id,
            type=interrupt_type,
            message=message
        )

        self._pending_interrupts[subagent_id] = request
        logger.debug(
            f"Added {interrupt_type} interrupt for subagent [{subagent_id}]: {message}"
        )

        return request

    async def cancel_interrupt(self, request_id: str):
        """
        Cancel a pending interrupt.

        Args:
            request_id: Interrupt request ID to cancel
        """
        to_remove = []
        for subagent_id, request in self._pending_interrupts.items():
            if request.request_id == request_id:
                to_remove.append(subagent_id)
                logger.debug(f"Cancelled interrupt {request_id} for subagent [{subagent_id}]")

        for subagent_id in to_remove:
            del self._pending_interrupts[subagent_id]

    def is_subagent_paused(self, subagent_id: str) -> bool:
        """Check if a subagent is currently paused."""
        return subagent_id in self._paused_subagents

    def get_pending_interrupts(self) -> Dict[str, InterruptRequest]:
        """Get all pending interrupt requests."""
        return self._pending_interrupts.copy()

    def get_paused_subagents(self) -> Set[str]:
        """Get all currently paused subagents."""
        return self._paused_subagents.copy()

    def get_interrupt_type(self, interrupt_type: str) -> Optional[InterruptType]:
        """Get interrupt type details."""
        return self._interrupt_types.get(interrupt_type)

    async def cancel_all_pending_interrupts(self):
        """Cancel all pending interrupts."""
        count = len(self._pending_interrupts)
        self._pending_interrupts.clear()
        logger.info(f"Cancelled {count} pending interrupts")

    async def pause_all_subagents(self):
        """Pause all running subagents."""
        for subagent_id, subagent in self.manager._subagent_map.items():
            if subagent.status == "running" and subagent_id not in self._paused_subagents:
                self._paused_subagents.add(subagent_id)

        logger.info(f"Paused {len(self._paused_subagents)} subagents")

    async def resume_all_subagents(self):
        """Resume all paused subagents."""
        count = len(self._paused_subagents)
        self._paused_subagents.clear()
        logger.info(f"Resumed {count} subagents")

    async def handle_message_interrupt(self, message: InboundMessage):
        """
        Handle interrupt from message bus.

        Args:
            message: Inbound message containing interrupt request

        Returns:
            True if message was handled as interrupt
        """
        content = message.content.lower()

        # Detect interrupt commands in message
        if "cancel" in content and "subagent" in content:
            subagent_id = await self._extract_subagent_id(content)
            if subagent_id:
                await self.add_interrupt(subagent_id, "cancel", message.content)
                return True
        elif "pause" in content and "subagent" in content:
            subagent_id = await self._extract_subagent_id(content)
            if subagent_id:
                await self.add_interrupt(subagent_id, "pause", message.content)
                return True
        elif "resume" in content and "subagent" in content:
            subagent_id = await self._extract_subagent_id(content)
            if subagent_id:
                await self.add_interrupt(subagent_id, "resume", message.content)
                return True
        elif "correct" in content and "subagent" in content:
            subagent_id = await self._extract_subagent_id(content)
            if subagent_id:
                # Extract new task from message
                new_task = await self._extract_correction_task(content)
                await self.add_interrupt(subagent_id, "correct", new_task)
                return True
        elif "status" in content and "subagent" in content:
            subagent_id = await self._extract_subagent_id(content)
            if subagent_id:
                await self.add_interrupt(subagent_id, "status", message.content)
                return True

        return False

    async def _extract_subagent_id(self, content: str) -> Optional[str]:
        """Extract subagent ID from message content."""
        import re
        match = re.search(r'\[([a-z0-9]{8})\]', content)
        if match:
            return match.group(1)

        # Look for subagent ID patterns
        match = re.search(r'subagent\s+(\w+)', content)
        if match:
            return match.group(1)

        return None

    async def _extract_correction_task(self, content: str) -> str:
        """Extract correction task from message content."""
        # Remove interrupt prefix and subagent ID
        content = content.replace("correct", "", 1)
        content = content.replace("subagent", "", 1)

        # Remove any subagent ID patterns
        import re
        content = re.sub(r'\[[a-z0-9]{8}\]', '', content)
        content = re.sub(r'subagent\s+\w+', '', content)

        return content.strip()

    async def wait_for_resume(self, subagent_id: str, timeout: int = 300) -> bool:
        """
        Wait for resume interrupt.

        Args:
            subagent_id: Subagent ID to wait for
            timeout: Timeout in seconds

        Returns:
            True if resumed, False if timeout
        """
        start_time = datetime.now()
        while subagent_id in self._paused_subagents:
            if (datetime.now() - start_time).total_seconds() > timeout:
                logger.warning(f"Resume timeout for subagent [{subagent_id}]")
                return False

            await asyncio.sleep(1)

        return True
