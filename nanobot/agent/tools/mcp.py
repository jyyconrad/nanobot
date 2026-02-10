"""MCP (Model Context Protocol) tool for agent operations."""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from loguru import logger

from nanobot.agent.tools.base import Tool


@dataclass
class MCPToolConfig:
    """Configuration for a single MCP server."""
    server_url: str
    server_name: str
    auth_token: str
    auth_type: str = "bearer"


class MCPTool(Tool):
    """Tool to interact with Model Context Protocol."""

    name = "mcp"
    description = "MCP - Interact with Model Context Protocol"

    def __init__(self, config: Optional[List[MCPToolConfig]] = None):
        """Initialize MCP tool.

        Args:
            config: Optional configuration list for MCP servers
        """
        self.config = config or []
        self._initialized = False
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.tools: Dict[str, Dict[str, Any]] = {}

    async def _initialize(self):
        """Initialize MCP connections to all configured servers."""
        if self._initialized:
            return

        try:
            # TODO: Initialize actual MCP connections
            # For now, just mark as initialized
            for server_config in self.config:
                self.servers[server_config.server_name] = {
                    "config": server_config,
                    "client": None,  # Placeholder for actual client
                }
            self._initialized = True
            logger.debug(f"MCP tool initialized with {len(self.servers)} servers")
        except Exception as e:
            logger.error(f"Failed to initialize MCP tool: {e}")
            raise

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "MCP operation to perform",
                    "enum": ["list", "discover", "call"],
                },
                "tool_name": {
                    "type": "string",
                    "description": "Tool name for call operation",
                },
                "params": {
                    "type": "object",
                    "description": "Parameters for tool call",
                },
            },
            "required": ["operation"],
        }

    async def execute(self, operation: str, **kwargs) -> str:
        """Execute MCP tool operation.

        Args:
            operation: Operation to perform (list, discover, call)
            **kwargs: Additional parameters

        Returns:
            Operation result
        """
        await self._initialize()

        try:
            if operation == "list":
                return self._list_tools()
            elif operation == "discover":
                return self._discover_servers()
            elif operation == "call":
                return await self._call_tool(**kwargs)
            else:
                return f"Unknown operation: {operation}"
        except Exception as e:
            logger.error(f"Error executing MCP tool: {e}")
            return f"Error executing MCP tool: {e}"

    def _list_tools(self) -> str:
        """List all available tools from all servers.

        Returns:
            Formatted list of tools
        """
        if not self.tools:
            return "No tools available"

        result = []
        for tool_name, tool_info in self.tools.items():
            server_name = tool_info["server"]
            tool_desc = tool_info.get("tool", {}).get("description", "No description")
            result.append(f"- {tool_name} (from {server_name}): {tool_desc}")

        return "\n".join(result)

    def _discover_servers(self) -> str:
        """Discover all connected MCP servers.

        Returns:
            Formatted server list
        """
        if not self.servers:
            return "No servers connected"

        result = []
        for server_name, server_info in self.servers.items():
            server_config = server_info["config"]
            tool_count = sum(1 for t in self.tools.values() if t["server"] == server_name)
            result.append(f"- {server_name}: ({tool_count} tools)")

        return "\n".join(result)

    async def _call_tool(
        self, tool_name: str, params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Call a specific MCP tool.

        Args:
            tool_name: Tool name in format "server:tool"
            params: Tool parameters

        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            return f"Tool not found: {tool_name}"

        tool_info = self.tools[tool_name]
        server_name = tool_info["server"]
        server_info = self.servers[server_name]

        # Try to call actual MCP tool using litellm
        try:
            from litellm.experimental_mcp_client.tools import call_mcp_tool

            result = await call_mcp_tool(tool_name, params or {})
            return str(result)
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Error calling MCP tool: {e}")

        # Fallback: return mock result
        logger.debug(f"Calling tool {tool_name} with params: {params}")
        return "Result: Mock tool execution"

    def to_schema(self) -> Dict[str, Any]:
        """Convert tool to OpenAI function schema.

        Returns:
            Function schema
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def validate_params(self, params: Dict[str, Any]) -> List[str]:
        """Validate tool parameters.

        Args:
            params: Parameters to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check operation
        if "operation" not in params:
            errors.append("operation is required")
            return errors

        operation = params["operation"]
        valid_operations = ["list", "discover", "call"]

        if operation not in valid_operations:
            errors.append(f"Unknown operation: {operation}. Valid: {valid_operations}")
            return errors

        # Validate call operation parameters
        if operation == "call":
            if "tool_name" not in params:
                errors.append("tool_name is required for call operation")
            if "params" not in params:
                errors.append("params is required for call operation")

        return errors
