"""High-risk operation evaluation for Human-in-loop decision making."""

import re
from typing import Any, List, Optional, Set

from loguru import logger
from pydantic import BaseModel, Field

from nanobot.agent.subagent.agno_subagent import AgnoSubagentManager
from nanobot.bus.events import InboundMessage
from nanobot.bus.queue import MessageBus


class RiskLevel(BaseModel):
    """Risk level classification model."""

    level: str = Field(..., description="Risk level: low, medium, high, critical")
    score: int = Field(..., description="Risk score (0-100)")
    description: str = Field(..., description="Risk description")
    requires_approval: bool = Field(..., description="Whether human approval is required")


class RiskAssessment(BaseModel):
    """Risk assessment result model."""

    tool_name: str = Field(..., description="Name of the tool being evaluated")
    arguments: dict = Field(..., description="Tool arguments")
    risk_level: RiskLevel = Field(..., description="Risk level assessment")
    rationale: str = Field(..., description="Rationale for the assessment")
    mitigation: Optional[str] = Field(default=None, description="Mitigation suggestions")


class RiskEvaluator:
    """
    Risk evaluator for high-risk operation assessment.

    This component evaluates tool calls to determine their risk level
    and whether human approval is required before execution.
    """

    def __init__(self, manager: AgnoSubagentManager):
        self.manager = manager
        self.bus: MessageBus = manager.bus
        self._high_risk_tools: Set[str] = {"exec"}
        self._restricted_commands: Set[str] = {
            "rm",
            "rmdir",
            "rm -rf",
            "sudo",
            "su",
            "chmod",
            "chown",
            "mv",
            "dd",
            "format",
            "mkfs",
            "fdisk",
            "parted",
            "wipefs",
            "shred",
            "unlink",
        }
        self._dangerous_patterns: List[str] = [
            r"rm\s+-rf",
            r"sudo\s+.*",
            r"su\s+.*",
            r"chmod\s+777",
            r"dd\s+.*of=",
            r"mkfs\s+.*",
            r"fdisk\s+.*",
            r"parted\s+.*",
            r"wipefs\s+.*",
            r"shred\s+.*",
        ]

    async def evaluate_tool_calls(self, subagent_id: str, tool_calls: List[Any]) -> bool:
        """
        Evaluate tool calls for risk and determine if they should be allowed.

        Args:
            subagent_id: ID of the subagent making the tool calls
            tool_calls: List of tool calls to evaluate

        Returns:
            True if all tool calls are safe to execute, False if human approval is required
        """
        assessments = []

        for tc in tool_calls:
            assessment = await self._evaluate_single_tool_call(subagent_id, tc)
            assessments.append(assessment)

            # Check if any tool call requires approval
            if assessment.risk_level.requires_approval:
                logger.warning(
                    f"High-risk operation detected: {assessment.tool_name} "
                    f"with arguments {assessment.arguments}"
                )
                await self._request_approval(subagent_id, assessment)
                return False

        logger.debug(f"All tool calls evaluated as safe: {[a.tool_name for a in assessments]}")
        return True

    async def _evaluate_single_tool_call(self, subagent_id: str, tool_call: Any) -> RiskAssessment:
        """Evaluate a single tool call for risk."""
        tool_name = tool_call.name
        arguments = tool_call.arguments

        if tool_name in self._high_risk_tools:
            return await self._evaluate_high_risk_tool(subagent_id, tool_name, arguments)
        else:
            return await self._evaluate_low_risk_tool(subagent_id, tool_name, arguments)

    async def _evaluate_high_risk_tool(
        self, subagent_id: str, tool_name: str, arguments: dict
    ) -> RiskAssessment:
        """Evaluate high-risk tools like shell commands."""
        command = arguments.get("command", "")

        # Check for restricted commands
        risk_score = 50
        risk_level = "medium"
        rationale = "High-risk tool call (shell command)"

        if any(cmd in command.lower() for cmd in self._restricted_commands):
            risk_score = 90
            risk_level = "critical"
            rationale = f"Restricted command detected: {command}"

        # Check for dangerous patterns
        for pattern in self._dangerous_patterns:
            if re.search(pattern, command.lower()):
                risk_score = 95
                risk_level = "critical"
                rationale = f"Dangerous command pattern detected: {command}"

        # Check command complexity and scope
        if len(command.split()) > 10:
            risk_score += 10
            rationale += " (Complex command)"

        if ".." in command or command.startswith("/"):
            risk_score += 15
            rationale += " (Absolute path or parent directory access)"

        # Cap risk score at 100
        risk_score = min(risk_score, 100)

        risk_level_obj = RiskLevel(
            level=risk_level,
            score=risk_score,
            description=self._get_risk_description(risk_level),
            requires_approval=risk_score >= 70,
        )

        mitigation = await self._get_mitigation_suggestions(tool_name, arguments, risk_level)

        return RiskAssessment(
            tool_name=tool_name,
            arguments=arguments,
            risk_level=risk_level_obj,
            rationale=rationale,
            mitigation=mitigation,
        )

    async def _evaluate_low_risk_tool(
        self, subagent_id: str, tool_name: str, arguments: dict
    ) -> RiskAssessment:
        """Evaluate low-risk tools like read file, list dir, etc."""
        risk_level = RiskLevel(
            level="low", score=10, description="Low-risk operation", requires_approval=False
        )

        return RiskAssessment(
            tool_name=tool_name,
            arguments=arguments,
            risk_level=risk_level,
            rationale=f"Low-risk tool call: {tool_name}",
            mitigation=None,
        )

    async def _request_approval(self, subagent_id: str, assessment: RiskAssessment):
        """Request human approval for high-risk operation."""
        approval_content = f"""**High-Risk Operation Detection**

Agno Subagent [{subagent_id}] is attempting to execute a high-risk operation:

**Tool:** {assessment.tool_name}
**Risk Level:** {assessment.risk_level.level} ({assessment.risk_level.score}/100)
**Arguments:** {assessment.arguments}
**Rationale:** {assessment.rationale}
**Mitigation:** {assessment.mitigation or "None"}

Please review this operation. Do you want to allow it to proceed?
"""

        msg = InboundMessage(
            channel="system",
            sender_id="risk_evaluator",
            chat_id="approval_needed",
            content=approval_content,
        )

        await self.bus.publish_inbound(msg)
        logger.debug(f"Approval requested for subagent {subagent_id}")

    async def approve_operation(self, subagent_id: str, assessment: RiskAssessment) -> bool:
        """Approve a high-risk operation."""
        logger.info(f"High-risk operation approved for subagent [{subagent_id}]")
        return True

    async def reject_operation(self, subagent_id: str, assessment: RiskAssessment) -> bool:
        """Reject a high-risk operation."""
        logger.warning(f"High-risk operation rejected for subagent [{subagent_id}]")
        return False

    def _get_risk_description(self, level: str) -> str:
        """Get risk level description."""
        descriptions = {
            "low": "Low-risk operation. No human approval required.",
            "medium": "Medium-risk operation. Exercise caution.",
            "high": "High-risk operation. May impact system stability or data integrity.",
            "critical": "Critical risk operation. May cause system damage or data loss.",
        }
        return descriptions.get(level, "Unknown risk level")

    async def _get_mitigation_suggestions(
        self, tool_name: str, arguments: dict, risk_level: str
    ) -> Optional[str]:
        """Get mitigation suggestions based on tool and arguments."""
        if risk_level == "critical":
            return "This operation is highly dangerous. Consider alternatives or review the command carefully."

        if tool_name == "exec":
            command = arguments.get("command", "")
            if "rm" in command and "-rf" in command:
                return "Consider using trash instead of rm -rf to allow recovery."
            if "sudo" in command:
                return "Avoid using sudo if possible. Consider lower privileges."

        return None

    def add_restricted_command(self, command: str):
        """Add a command to the restricted commands list."""
        self._restricted_commands.add(command.lower())
        logger.debug(f"Added restricted command: {command}")

    def remove_restricted_command(self, command: str):
        """Remove a command from the restricted commands list."""
        self._restricted_commands.discard(command.lower())
        logger.debug(f"Removed restricted command: {command}")

    def add_dangerous_pattern(self, pattern: str):
        """Add a dangerous command pattern."""
        self._dangerous_patterns.append(pattern)
        logger.debug(f"Added dangerous pattern: {pattern}")

    def remove_dangerous_pattern(self, pattern: str):
        """Remove a dangerous command pattern."""
        if pattern in self._dangerous_patterns:
            self._dangerous_patterns.remove(pattern)
            logger.debug(f"Removed dangerous pattern: {pattern}")

    def is_high_risk_tool(self, tool_name: str) -> bool:
        """Check if a tool is considered high-risk."""
        return tool_name in self._high_risk_tools

    async def evaluate_custom_tool(self, tool_name: str, arguments: dict) -> RiskAssessment:
        """
        Evaluate a custom tool call.

        Args:
            tool_name: Name of the custom tool
            arguments: Tool arguments

        Returns:
            Risk assessment
        """
        return await self._evaluate_single_tool_call(
            "custom", type("ToolCall", (object,), {"name": tool_name, "arguments": arguments})
        )

    async def evaluate_command_safety(self, command: str) -> RiskAssessment:
        """
        Evaluate the safety of a shell command.

        Args:
            command: Shell command to evaluate

        Returns:
            Risk assessment
        """
        return await self._evaluate_single_tool_call(
            "custom",
            type("ToolCall", (object,), {"name": "exec", "arguments": {"command": command}}),
        )
