"""Tests for MCP tool."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from nanobot.agent.tools.mcp import MCPTool, MCPToolConfig


@pytest.fixture
def mcp_tool():
    """Create a mock MCP tool."""
    config = [
        MCPToolConfig(
            server_url="https://github.com/mcp",
            server_name="github_mcp",
            auth_token="test_token",
            auth_type="bearer",
        ),
        MCPToolConfig(
            server_url="https://zapier.com/mcp",
            server_name="zapier_mcp",
            auth_token="test_token",
            auth_type="bearer",
        ),
    ]
    return MCPTool(config=config)


class TestMCPTool:
    """Tests for MCPTool class."""

    def test_initialization(self, mcp_tool):
        """Test MCP tool initialization."""
        assert mcp_tool.name == "mcp"
        assert "MCP" in mcp_tool.description
        assert len(mcp_tool.config) == 2
        assert not mcp_tool._initialized
        assert len(mcp_tool.servers) == 0
        assert len(mcp_tool.tools) == 0

    @patch("nanobot.agent.tools.mcp.MCPTool._initialize")
    async def test_execute_list_operation(self, mock_initialize, mcp_tool):
        """Test execute method with list operation."""
        # Setup mock
        mock_initialize.return_value = None
        mcp_tool.tools = {
            "github_mcp:list_repositories": {
                "tool": Mock(name="list_repositories", description="List repositories"),
                "server": "github_mcp",
            },
            "github_mcp:create_issue": {
                "tool": Mock(name="create_issue", description="Create issue"),
                "server": "github_mcp",
            },
        }

        # Test
        result = await mcp_tool.execute(operation="list")
        assert "list_repositories" in result
        assert "create_issue" in result
        mock_initialize.assert_called_once()

    @patch("nanobot.agent.tools.mcp.MCPTool._initialize")
    async def test_execute_discover_operation(self, mock_initialize, mcp_tool):
        """Test execute method with discover operation."""
        # Setup mock
        mock_initialize.return_value = None
        mcp_tool.servers = {
            "github_mcp": {
                "config": Mock(server_url="https://github.com/mcp"),
                "client": Mock(),
            },
            "zapier_mcp": {
                "config": Mock(server_url="https://zapier.com/mcp"),
                "client": Mock(),
            },
        }
        mcp_tool.tools = {
            "github_mcp:list_repositories": {"tool": Mock(), "server": "github_mcp"},
            "zapier_mcp:list_zaps": {"tool": Mock(), "server": "zapier_mcp"},
        }

        # Test
        result = await mcp_tool.execute(operation="discover")
        assert "github_mcp" in result
        assert "zapier_mcp" in result
        assert "(1 tools)" in result
        mock_initialize.assert_called_once()

    @patch("nanobot.agent.tools.mcp.MCPTool._initialize")
    async def test_execute_call_operation(self, mock_initialize, mcp_tool):
        """Test execute method with call operation."""
        # Setup mock
        mock_initialize.return_value = None

        # Create mock tool and server
        mock_tool = Mock(name="list_repositories")
        mock_tool.name = "list_repositories"
        mock_tool.description = "List repositories"

        mock_client = Mock()
        mock_client.session = Mock()

        mcp_tool.tools = {
            "github_mcp:list_repositories": {
                "tool": mock_tool,
                "server": "github_mcp",
            },
        }
        mcp_tool.servers = {
            "github_mcp": {
                "config": Mock(server_url="https://github.com/mcp"),
                "client": mock_client,
            },
        }

        # Test
        with patch("litellm.experimental_mcp_client.tools.call_mcp_tool") as mock_call_tool:
            # 修复：直接模拟原始导入位置的 call_mcp_tool 函数
            mock_call_tool.return_value = "Result: [repo1, repo2]"
            result = await mcp_tool.execute(
                operation="call",
                tool_name="github_mcp:list_repositories",
                params={"owner": "test"},
            )
            assert "Result" in result
            mock_call_tool.assert_called_once()
            mock_initialize.assert_called_once()

    @patch("nanobot.agent.tools.mcp.MCPTool._initialize")
    async def test_execute_unknown_operation(self, mock_initialize, mcp_tool):
        """Test execute method with unknown operation."""
        result = await mcp_tool.execute(operation="unknown")
        assert "Unknown operation" in result
        mock_initialize.assert_called_once()

    def test_to_schema(self, mcp_tool):
        """Test to_schema method."""
        schema = mcp_tool.to_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "mcp"
        assert "MCP" in schema["function"]["description"]
        assert "parameters" in schema["function"]

    def test_validate_params_valid(self, mcp_tool):
        """Test validate_params with valid parameters."""
        # Test list operation
        errors = mcp_tool.validate_params({"operation": "list"})
        assert len(errors) == 0

        # Test discover operation
        errors = mcp_tool.validate_params({"operation": "discover"})
        assert len(errors) == 0

        # Test call operation
        errors = mcp_tool.validate_params(
            {
                "operation": "call",
                "tool_name": "test_tool",
                "params": {"key": "value"},
            }
        )
        assert len(errors) == 0

    def test_validate_params_invalid(self, mcp_tool):
        """Test validate_params with invalid parameters."""
        # Missing operation
        errors = mcp_tool.validate_params({})
        assert len(errors) == 1
        assert "required" in errors[0]

        # Invalid operation
        errors = mcp_tool.validate_params({"operation": "invalid"})
        assert len(errors) == 1
        assert "Unknown operation" in errors[0]

        # Missing tool_name for call
        errors = mcp_tool.validate_params({"operation": "call", "params": {}})
        assert len(errors) == 1
        assert "tool_name" in errors[0]

        # Missing params for call
        errors = mcp_tool.validate_params({"operation": "call", "tool_name": "test"})
        assert len(errors) == 1
        assert "params" in errors[0]
