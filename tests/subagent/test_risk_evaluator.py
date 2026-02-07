"""Tests for RiskEvaluator component."""

from unittest.mock import MagicMock, patch

import pytest

from nanobot.agent.subagent.agno_subagent import AgnoSubagentManager
from nanobot.agent.subagent.risk_evaluator import RiskAssessment, RiskEvaluator, RiskLevel


@pytest.fixture
def mock_manager():
    """Create a mock AgnoSubagentManager."""
    manager = MagicMock(spec=AgnoSubagentManager)
    manager.bus = MagicMock()
    manager.bus.publish_inbound = MagicMock()
    return manager


class TestRiskLevel:
    """Tests for RiskLevel model."""

    def test_risk_level_creation(self):
        """Test RiskLevel initialization."""
        risk_level = RiskLevel(
            level="high", score=85, description="High risk operation", requires_approval=True
        )

        assert risk_level.level == "high"
        assert risk_level.score == 85
        assert risk_level.description == "High risk operation"
        assert risk_level.requires_approval is True

    def test_risk_level_comparison(self):
        """Test risk level comparison based on score."""
        low_risk = RiskLevel(level="low", score=20, description="Low risk", requires_approval=False)
        high_risk = RiskLevel(
            level="high", score=80, description="High risk", requires_approval=True
        )

        assert high_risk.score > low_risk.score
        assert high_risk.requires_approval != low_risk.requires_approval


class TestRiskAssessment:
    """Tests for RiskAssessment model."""

    def test_risk_assessment_creation(self):
        """Test RiskAssessment initialization."""
        risk_level = RiskLevel(
            level="medium", score=55, description="Medium risk operation", requires_approval=False
        )

        assessment = RiskAssessment(
            tool_name="exec",
            arguments={"command": "rm -rf temp"},
            risk_level=risk_level,
            rationale="Dangerous command pattern detected",
            mitigation="Use trash instead of rm -rf",
        )

        assert assessment.tool_name == "exec"
        assert assessment.arguments == {"command": "rm -rf temp"}
        assert assessment.risk_level == risk_level
        assert assessment.rationale == "Dangerous command pattern detected"
        assert assessment.mitigation == "Use trash instead of rm -rf"


class TestRiskEvaluator:
    """Tests for RiskEvaluator component."""

    def test_initialization(self, mock_manager):
        """Test RiskEvaluator initialization."""
        evaluator = RiskEvaluator(mock_manager)

        assert evaluator.manager == mock_manager
        assert evaluator.bus == mock_manager.bus
        assert len(evaluator._high_risk_tools) > 0
        assert len(evaluator._restricted_commands) > 0
        assert len(evaluator._dangerous_patterns) > 0

    def test_is_high_risk_tool(self, mock_manager):
        """Test if a tool is considered high-risk."""
        evaluator = RiskEvaluator(mock_manager)

        assert evaluator.is_high_risk_tool("exec") is True
        assert evaluator.is_high_risk_tool("read_file") is False
        assert evaluator.is_high_risk_tool("write_file") is False
        assert evaluator.is_high_risk_tool("list_dir") is False

    def test_add_restricted_command(self, mock_manager):
        """Test adding restricted command."""
        evaluator = RiskEvaluator(mock_manager)
        original_count = len(evaluator._restricted_commands)

        evaluator.add_restricted_command("cp -r")
        assert len(evaluator._restricted_commands) == original_count + 1
        assert "cp -r" in evaluator._restricted_commands

    def test_remove_restricted_command(self, mock_manager):
        """Test removing restricted command."""
        evaluator = RiskEvaluator(mock_manager)
        evaluator.add_restricted_command("cp -r")

        evaluator.remove_restricted_command("cp -r")
        assert "cp -r" not in evaluator._restricted_commands

    def test_add_dangerous_pattern(self, mock_manager):
        """Test adding dangerous pattern."""
        evaluator = RiskEvaluator(mock_manager)
        original_count = len(evaluator._dangerous_patterns)

        evaluator.add_dangerous_pattern(r"chmod\s+777")
        assert len(evaluator._dangerous_patterns) == original_count + 1
        assert r"chmod\s+777" in evaluator._dangerous_patterns

    def test_remove_dangerous_pattern(self, mock_manager):
        """Test removing dangerous pattern."""
        evaluator = RiskEvaluator(mock_manager)
        pattern = r"chmod\s+777"
        original_length = len(evaluator._dangerous_patterns)
        evaluator.add_dangerous_pattern(pattern)

        assert len(evaluator._dangerous_patterns) == original_length + 1

        evaluator.remove_dangerous_pattern(pattern)
        assert len(evaluator._dangerous_patterns) == original_length

    @pytest.mark.asyncio
    async def test_evaluate_low_risk_tool(self, mock_manager):
        """Test evaluating a low-risk tool."""
        evaluator = RiskEvaluator(mock_manager)

        tool_call = MagicMock()
        tool_call.name = "read_file"
        tool_call.arguments = {"path": "test.txt"}

        assessment = await evaluator._evaluate_single_tool_call("test-1234", tool_call)

        assert assessment.tool_name == "read_file"
        assert assessment.risk_level.level == "low"
        assert assessment.risk_level.score == 10
        assert assessment.risk_level.requires_approval is False

    @pytest.mark.asyncio
    async def test_evaluate_high_risk_tool(self, mock_manager):
        """Test evaluating a high-risk tool."""
        evaluator = RiskEvaluator(mock_manager)

        tool_call = MagicMock()
        tool_call.name = "exec"
        tool_call.arguments = {"command": "ls -la", "workdir": "/tmp"}

        assessment = await evaluator._evaluate_single_tool_call("test-1234", tool_call)

        assert assessment.tool_name == "exec"
        assert assessment.risk_level.level == "medium"
        assert assessment.risk_level.score >= 50
        assert assessment.risk_level.score < 70
        assert assessment.risk_level.requires_approval is False

    @pytest.mark.asyncio
    async def test_evaluate_restricted_command(self, mock_manager):
        """Test evaluating a restricted command."""
        evaluator = RiskEvaluator(mock_manager)

        tool_call = MagicMock()
        tool_call.name = "exec"
        tool_call.arguments = {"command": "rm -rf /tmp", "workdir": "/tmp"}

        assessment = await evaluator._evaluate_single_tool_call("test-1234", tool_call)

        assert assessment.tool_name == "exec"
        assert assessment.risk_level.level == "critical"
        assert assessment.risk_level.score > 90
        assert assessment.risk_level.requires_approval is True
        assert (
            "Restricted command detected" in assessment.rationale
            or "Dangerous command pattern detected" in assessment.rationale
        )

    @pytest.mark.asyncio
    async def test_evaluate_dangerous_pattern(self, mock_manager):
        """Test evaluating a command with dangerous pattern."""
        evaluator = RiskEvaluator(mock_manager)

        tool_call = MagicMock()
        tool_call.name = "exec"
        tool_call.arguments = {"command": "sudo rm -rf /", "workdir": "/"}

        assessment = await evaluator._evaluate_single_tool_call("test-1234", tool_call)

        assert assessment.tool_name == "exec"
        assert assessment.risk_level.level == "critical"
        assert assessment.risk_level.score > 90
        assert assessment.risk_level.requires_approval is True

    @pytest.mark.asyncio
    async def test_evaluate_command_safety(self, mock_manager):
        """Test evaluating command safety."""
        evaluator = RiskEvaluator(mock_manager)

        safe_result = await evaluator.evaluate_command_safety("ls -la")
        assert safe_result.risk_level.level == "medium"
        assert safe_result.risk_level.requires_approval is False

        dangerous_result = await evaluator.evaluate_command_safety("sudo rm -rf /")
        assert dangerous_result.risk_level.level == "critical"
        assert dangerous_result.risk_level.requires_approval is True

    @pytest.mark.asyncio
    async def test_evaluate_custom_tool(self, mock_manager):
        """Test evaluating custom tool calls."""
        evaluator = RiskEvaluator(mock_manager)

        result = await evaluator.evaluate_custom_tool("read_file", {"path": "test.txt"})
        assert result.tool_name == "read_file"
        assert result.risk_level.level == "low"

        result = await evaluator.evaluate_custom_tool("exec", {"command": "rm -rf temp"})
        assert result.tool_name == "exec"
        assert result.risk_level.requires_approval is True

    @pytest.mark.asyncio
    async def test_evaluate_tool_calls_approve_all(self, mock_manager):
        """Test evaluating tool calls that are all safe to approve."""
        evaluator = RiskEvaluator(mock_manager)

        tool_call1 = MagicMock()
        tool_call1.name = "read_file"
        tool_call1.arguments = {"path": "test.txt"}

        tool_call2 = MagicMock()
        tool_call2.name = "write_file"
        tool_call2.arguments = {"path": "output.txt", "content": "test"}

        result = await evaluator.evaluate_tool_calls("test-1234", [tool_call1, tool_call2])
        assert result is True

    @pytest.mark.asyncio
    async def test_evaluate_tool_calls_require_approval(self, mock_manager):
        """Test evaluating tool calls that require human approval."""
        evaluator = RiskEvaluator(mock_manager)

        tool_call1 = MagicMock()
        tool_call1.name = "read_file"
        tool_call1.arguments = {"path": "test.txt"}

        tool_call2 = MagicMock()
        tool_call2.name = "exec"
        tool_call2.arguments = {"command": "sudo rm -rf /"}

        with patch.object(evaluator, "_request_approval") as mock_request:
            result = await evaluator.evaluate_tool_calls("test-1234", [tool_call1, tool_call2])
            assert result is False
            assert mock_request.called

    @pytest.mark.asyncio
    async def test_request_approval(self, mock_manager):
        """Test requesting approval for high-risk operations."""
        evaluator = RiskEvaluator(mock_manager)

        assessment = RiskAssessment(
            tool_name="exec",
            arguments={"command": "sudo rm -rf /"},
            risk_level=RiskLevel(
                level="critical", score=95, description="Critical risk", requires_approval=True
            ),
            rationale="Dangerous command pattern detected",
            mitigation="Avoid this command",
        )

        # Make the mock publish method awaitable
        async def mock_publish(msg):
            pass

        mock_manager.bus.publish_inbound = mock_publish

        await evaluator._request_approval("test-1234", assessment)

    @pytest.mark.asyncio
    async def test_approve_operation(self, mock_manager):
        """Test approving an operation."""
        evaluator = RiskEvaluator(mock_manager)

        assessment = RiskAssessment(
            tool_name="exec",
            arguments={"command": "rm -rf temp"},
            risk_level=RiskLevel(
                level="high", score=80, description="High risk", requires_approval=True
            ),
            rationale="Dangerous command pattern",
            mitigation="Use trash",
        )

        result = await evaluator.approve_operation("test-1234", assessment)
        assert result is True

    @pytest.mark.asyncio
    async def test_reject_operation(self, mock_manager):
        """Test rejecting an operation."""
        evaluator = RiskEvaluator(mock_manager)

        assessment = RiskAssessment(
            tool_name="exec",
            arguments={"command": "rm -rf temp"},
            risk_level=RiskLevel(
                level="high", score=80, description="High risk", requires_approval=True
            ),
            rationale="Dangerous command pattern",
            mitigation="Use trash",
        )

        result = await evaluator.reject_operation("test-1234", assessment)
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
