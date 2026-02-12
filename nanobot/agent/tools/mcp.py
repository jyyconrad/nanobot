"""MCP (Model Context Protocol) tool for agent operations."""

import asyncio
import json
import subprocess
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from loguru import logger

from nanobot.agent.tools.base import Tool


@dataclass
class MCPToolConfig:
    """Configuration for a single MCP server."""
    server_name: str
    transport: str = "stdio"  # "stdio" or "sse"
    command: Optional[str] = None  # for stdio transport
    args: List[str] = field(default_factory=list)  # for stdio transport
    url: Optional[str] = None  # for sse transport
    env: Dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0


@dataclass
class MCPConnection:
    """Represents a connection to an MCP server."""
    config: MCPToolConfig
    process: Optional[subprocess.Popen] = None
    tools: List[Dict[str, Any]] = field(default_factory=list)
    initialized: bool = False
    request_id: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _pending_responses: Dict[int, asyncio.Future] = field(default_factory=dict)

    def get_next_request_id(self) -> int:
        """Get next request ID."""
        self.request_id += 1
        return self.request_id


class MCPTool(Tool):
    """Tool to interact with Model Context Protocol."""

    name = "mcp"
    description = "MCP - Interact with Model Context Protocol servers and tools"

    def __init__(self, config: Optional[List[MCPToolConfig]] = None):
        """Initialize MCP tool.

        Args:
            config: Optional configuration list for MCP servers
        """
        self.config = config or []
        self._initialized = False
        self.connections: Dict[str, MCPConnection] = {}
        self._all_tools: Dict[str, Dict[str, Any]] = {}  # tool_name -> {server, tool}

    async def _initialize(self):
        """Initialize MCP connections to all configured servers."""
        if self._initialized:
            return

        try:
            for server_config in self.config:
                await self._connect_to_server(server_config)

            self._initialized = True
            logger.info(f"MCP tool initialized with {len(self.connections)} servers, {len(self._all_tools)} tools")
        except Exception as e:
            logger.error(f"Failed to initialize MCP tool: {e}")
            raise

    async def _connect_to_server(self, config: MCPToolConfig) -> MCPConnection:
        """Connect to an MCP server.

        Args:
            config: Server configuration

        Returns:
            MCPConnection object
        """
        conn = MCPConnection(config=config)

        try:
            if config.transport == "stdio":
                await self._connect_stdio(conn)
            elif config.transport == "sse":
                await self._connect_sse(conn)
            else:
                raise ValueError(f"Unsupported transport: {config.transport}")

            # Initialize the connection
            await self._initialize_connection(conn)

            # List available tools
            await self._list_tools(conn)

            self.connections[config.server_name] = conn
            logger.debug(f"Connected to MCP server: {config.server_name}")

            return conn

        except Exception as e:
            logger.error(f"Failed to connect to MCP server {config.server_name}: {e}")
            raise

    async def _connect_stdio(self, conn: MCPConnection):
        """Connect via stdio transport."""
        config = conn.config

        if not config.command:
            raise ValueError("Command is required for stdio transport")

        env = {**config.env}

        conn.process = subprocess.Popen(
            [config.command] + config.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1,
        )

        logger.debug(f"Started MCP server process: {config.command}")

    async def _connect_sse(self, conn: MCPConnection):
        """Connect via SSE transport."""
        # SSE transport implementation would go here
        # This requires HTTP client with SSE support
        raise NotImplementedError("SSE transport not yet implemented")

    async def _initialize_connection(self, conn: MCPConnection):
        """Initialize the MCP connection."""
        if conn.config.transport == "stdio":
            # For stdio, we need to send initialize request
            # This is a simplified version - actual MCP protocol is more complex
            logger.debug("Initializing MCP stdio connection")
            conn.initialized = True
        else:
            conn.initialized = True

    async def _list_tools(self, conn: MCPConnection):
        """List available tools from the MCP server."""
        # This would make an actual MCP request to list tools
        # For now, we'll assume no tools are available until we implement full protocol
        logger.debug(f"Listing tools from {conn.config.server_name}")

        # In a full implementation, this would:
        # 1. Send a tools/list request
        # 2. Parse the response
        # 3. Store the tool definitions

        # For now, mark as empty list
        conn.tools = []

    async def _call_stdio_tool(
        self, conn: MCPConnection, tool_name: str, params: Dict[str, Any]
    ) -> str:
        """Call a tool via stdio transport."""
        import json

        if not conn.process or conn.process.poll() is not None:
            raise RuntimeError("MCP server process is not running")

        # Build the MCP request
        request_id = conn.get_next_request_id()
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params,
            },
        }

        # Send the request
        request_line = json.dumps(request) + "\n"
        conn.process.stdin.write(request_line)
        conn.process.stdin.flush()

        logger.debug(f"Sent MCP request: {request_line.strip()}")

        # Wait for response with timeout
        import select
        import time

        start_time = time.time()
        timeout = conn.config.timeout

        while time.time() - start_time < timeout:
            if conn.process.poll() is not None:
                raise RuntimeError("MCP server process terminated unexpectedly")

            # Check if data is available
            if select.select([conn.process.stdout], [], [], 0.1)[0]:
                response_line = conn.process.stdout.readline()
                if response_line:
                    try:
                        response = json.loads(response_line)
                        logger.debug(f"Received MCP response: {response}")

                        # Check if this is our response
                        if response.get("id") == request_id:
                            if "error" in response:
                                raise RuntimeError(f"MCP error: {response['error']}")
                            return json.dumps(response.get("result", {}))
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse MCP response: {response_line}")

            await asyncio.sleep(0.01)

        raise TimeoutError(f"MCP tool call timed out after {timeout} seconds")

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
        if not self._all_tools:
            return "No tools available. Connect to MCP servers first using 'discover' operation."

        result = []
        result.append(f"Available MCP Tools ({len(self._all_tools)} total):\n")

        # Group tools by server
        tools_by_server: Dict[str, List[str]] = {}
        for tool_name, tool_info in self._all_tools.items():
            server_name = tool_info.get("server", "unknown")
            if server_name not in tools_by_server:
                tools_by_server[server_name] = []
            tools_by_server[server_name].append(tool_name)

        for server_name, tool_names in tools_by_server.items():
            result.append(f"\n[{server_name}]")
            for tool_name in sorted(tool_names):
                tool_info = self._all_tools[tool_name]
                tool_desc = tool_info.get("description", "No description")
                result.append(f"  • {tool_name}: {tool_desc}")

        result.append("\n\nTo call a tool, use operation='call' with tool_name and params.")
        return "\n".join(result)

    def _discover_servers(self) -> str:
        """Discover all connected MCP servers.

        Returns:
            Formatted server list
        """
        if not self.connections:
            return "No MCP servers connected."

        result = []
        result.append(f"Connected MCP Servers ({len(self.connections)} total):\n")

        for server_name, conn in self.connections.items():
            config = conn.config
            tool_count = len(conn.tools)
            initialized = "✓" if conn.initialized else "✗"

            result.append(f"\n[{server_name}] {initialized}")
            result.append(f"  Transport: {config.transport}")
            if config.transport == "stdio":
                result.append(f"  Command: {config.command}")
            elif config.transport == "sse":
                result.append(f"  URL: {config.url}")
            result.append(f"  Tools: {tool_count}")
            result.append(f"  Timeout: {config.timeout}s")

        return "\n".join(result)

    async def _call_tool(
        self, tool_name: str, params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Call a specific MCP tool.

        Args:
            tool_name: Tool name (can be "server:tool" or just "tool")
            params: Tool parameters

        Returns:
            Tool execution result
        """
        params = params or {}

        # Parse tool name
        if ":" in tool_name:
            server_name, actual_tool_name = tool_name.split(":", 1)
        else:
            # Try to find tool in all servers
            if tool_name in self._all_tools:
                server_name = self._all_tools[tool_name].get("server", "")
                actual_tool_name = tool_name
            else:
                return f"Error: Tool '{tool_name}' not found. Use operation='list' to see available tools."

        # Find the connection
        if server_name not in self.connections:
            return f"Error: Server '{server_name}' not connected."

        conn = self.connections[server_name]

        if not conn.initialized:
            return f"Error: Server '{server_name}' not initialized."

        try:
            if conn.config.transport == "stdio":
                result = await self._call_stdio_tool(conn, actual_tool_name, params)
                return result
            elif conn.config.transport == "sse":
                return f"Error: SSE transport not yet implemented"
            else:
                return f"Error: Unknown transport: {conn.config.transport}"
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return f"Error calling tool '{tool_name}': {str(e)}"

    async def _discover_and_load_tools(self, conn: MCPConnection):
        """Discover and load tools from an MCP server.

        Args:
            conn: MCP connection
        """
        try:
            if conn.config.transport == "stdio" and conn.process:
                # Send tools/list request
                import json

                request_id = conn.get_next_request_id()
                request = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "tools/list",
                }

                request_line = json.dumps(request) + "\n"
                conn.process.stdin.write(request_line)
                conn.process.stdin.flush()

                # Wait for response
                import select
                import time

                start_time = time.time()
                timeout = conn.config.timeout

                while time.time() - start_time < timeout:
                    if conn.process.poll() is not None:
                        break

                    if select.select([conn.process.stdout], [], [], 0.1)[0]:
                        response_line = conn.process.stdout.readline()
                        if response_line:
                            try:
                                response = json.loads(response_line)
                                if response.get("id") == request_id:
                                    if "error" in response:
                                        logger.error(f"MCP tools/list error: {response['error']}")
                                    else:
                                        result = response.get("result", {})
                                        tools = result.get("tools", [])
                                        conn.tools = tools

                                        # Register tools
                                        for tool in tools:
                                            tool_name = tool.get("name", "")
                                            full_name = f"{conn.config.server_name}:{tool_name}"
                                            self._all_tools[full_name] = {
                                                "server": conn.config.server_name,
                                                "tool": tool,
                                                "description": tool.get("description", "No description"),
                                            }
                                            # Also register without prefix for simple lookups
                                            if tool_name not in self._all_tools:
                                                self._all_tools[tool_name] = {
                                                    "server": conn.config.server_name,
                                                    "tool": tool,
                                                    "description": tool.get("description", "No description"),
                                                }

                                        logger.info(f"Discovered {len(tools)} tools from {conn.config.server_name}")
                                    break
                            except json.JSONDecodeError:
                                pass

                    await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"Error discovering tools from {conn.config.server_name}: {e}")

    async def _connect_stdio(self, conn: MCPConnection):
        """Connect via stdio transport."""
        config = conn.config

        if not config.command:
            raise ValueError("Command is required for stdio transport")

        env = {**config.env}

        conn.process = subprocess.Popen(
            [config.command] + config.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1,
        )

        logger.debug(f"Started MCP server process: {config.command}")

        # Wait a moment for server to start
        await asyncio.sleep(0.5)

        if conn.process.poll() is not None:
            stderr = conn.process.stderr.read() if conn.process.stderr else ""
            raise RuntimeError(f"MCP server process terminated immediately. stderr: {stderr}")

        # Discover tools after successful connection
        await self._discover_and_load_tools(conn)

    async def _connect_sse(self, conn: MCPConnection):
        """Connect via SSE transport."""
        # SSE transport implementation would go here
        # This requires HTTP client with SSE support
        raise NotImplementedError("SSE transport not yet implemented")

    async def _call_stdio_tool(
        self, conn: MCPConnection, tool_name: str, params: Dict[str, Any]
    ) -> str:
        """Call a tool via stdio transport."""
        import json
        import select
        import time

        if not conn.process or conn.process.poll() is not None:
            raise RuntimeError("MCP server process is not running")

        # Build the MCP request
        request_id = conn.get_next_request_id()
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params,
            },
        }

        # Send the request
        request_line = json.dumps(request) + "\n"

        async with conn._lock:
            conn.process.stdin.write(request_line)
            conn.process.stdin.flush()

        logger.debug(f"Sent MCP request: {request_line.strip()}")

        # Create a future for the response
        future = asyncio.get_event_loop().create_future()
        conn._pending_responses[request_id] = future

        # Wait for response with timeout
        try:
            result = await asyncio.wait_for(
                future, timeout=conn.config.timeout
            )
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"MCP tool call timed out after {conn.config.timeout} seconds"
            )
        finally:
            conn._pending_responses.pop(request_id, None)

    async def _process_stdio_output(self, conn: MCPConnection):
        """Process output from stdio transport."""
        import json

        if not conn.process or not conn.process.stdout:
            return

        try:
            while conn.process and conn.process.poll() is None:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, conn.process.stdout.readline
                )

                if not line:
                    break

                try:
                    response = json.loads(line)
                    request_id = response.get("id")

                    # Check if there's a pending response
                    if request_id in conn._pending_responses:
                        future = conn._pending_responses[request_id]

                        if "error" in response:
                            future.set_exception(
                                RuntimeError(f"MCP error: {response['error']}")
                            )
                        else:
                            # Format the result
                            result = response.get("result", {})
                            content = result.get("content", [])

                            # Extract text content
                            texts = []
                            for item in content:
                                if item.get("type") == "text":
                                    texts.append(item.get("text", ""))

                            future.set_result("\n".join(texts))

                    # Handle server-initiated messages (notifications)
                    elif "method" in response:
                        logger.debug(f"Received MCP notification: {response['method']}")

                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse MCP output: {line}")

        except Exception as e:
            logger.error(f"Error processing MCP output: {e}")

    async def close(self):
        """Close all MCP connections."""
        for server_name, conn in self.connections.items():
            try:
                if conn.process and conn.process.poll() is None:
                    conn.process.terminate()
                    try:
                        conn.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        conn.process.kill()
                        conn.process.wait()

                    logger.debug(f"Closed MCP connection to {server_name}")
            except Exception as e:
                logger.error(f"Error closing MCP connection {server_name}: {e}")

        self.connections.clear()
        self._all_tools.clear()
        self._initialized = False

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
                    "description": "Tool name for call operation (format: 'server:tool' or just 'tool')",
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
        if not self._all_tools:
            return "No tools available. Connect to MCP servers first using 'discover' operation."

        result = []
        result.append(f"Available MCP Tools ({len(self._all_tools)} total):\n")

        # Group tools by server
        tools_by_server: Dict[str, List[str]] = {}
        for tool_name, tool_info in self._all_tools.items():
            server_name = tool_info.get("server", "unknown")
            if server_name not in tools_by_server:
                tools_by_server[server_name] = []
            tools_by_server[server_name].append(tool_name)

        for server_name, tool_names in tools_by_server.items():
            result.append(f"\n[{server_name}]")
            for tool_name in sorted(tool_names):
                tool_info = self._all_tools[tool_name]
                tool_desc = tool_info.get("description", "No description")
                # Truncate long descriptions
                if len(tool_desc) > 100:
                    tool_desc = tool_desc[:97] + "..."
                result.append(f"  • {tool_name}: {tool_desc}")

        result.append("\n\nTo call a tool, use operation='call' with tool_name and params.")
        result.append("Example: tool_name='filesystem:read_file', params={'path': '/tmp/test.txt'}")
        return "\n".join(result)

    def _discover_servers(self) -> str:
        """Discover all connected MCP servers.

        Returns:
            Formatted server list
        """
        if not self.connections:
            return "No MCP servers connected. Add server configurations to use MCP tools."

        result = []
        result.append(f"Connected MCP Servers ({len(self.connections)} total):\n")

        for server_name, conn in self.connections.items():
            config = conn.config
            tool_count = len(conn.tools)
            initialized = "✓ initialized" if conn.initialized else "✗ not initialized"

            result.append(f"\n[{server_name}] {initialized}")
            result.append(f"  Transport: {config.transport}")
            if config.transport == "stdio":
                result.append(f"  Command: {config.command}")
                if config.args:
                    result.append(f"  Args: {' '.join(config.args)}")
            elif config.transport == "sse":
                result.append(f"  URL: {config.url}")
            result.append(f"  Tools discovered: {tool_count}")
            result.append(f"  Timeout: {config.timeout}s")

        result.append("\n\nTo list available tools, use operation='list'.")
        return "\n".join(result)

    async def _call_tool(
        self, tool_name: str, params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Call a specific MCP tool.

        Args:
            tool_name: Tool name (can be "server:tool" or just "tool")
            params: Tool parameters

        Returns:
            Tool execution result
        """
        params = params or {}

        # Parse tool name
        if ":" in tool_name:
            server_name, actual_tool_name = tool_name.split(":", 1)
        else:
            # Try to find tool in all servers
            if tool_name in self._all_tools:
                server_name = self._all_tools[tool_name].get("server", "")
                actual_tool_name = tool_name
            else:
                return f"Error: Tool '{tool_name}' not found. Use operation='list' to see available tools."

        # Find the connection
        if server_name not in self.connections:
            return f"Error: Server '{server_name}' not connected."

        conn = self.connections[server_name]

        if not conn.initialized:
            return f"Error: Server '{server_name}' not initialized."

        try:
            if conn.config.transport == "stdio":
                result = await self._call_stdio_tool(conn, actual_tool_name, params)
                return result
            elif conn.config.transport == "sse":
                return f"Error: SSE transport not yet implemented"
            else:
                return f"Error: Unknown transport: {conn.config.transport}"
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return f"Error calling tool '{tool_name}': {str(e)}"

    async def _call_stdio_tool(
        self, conn: MCPConnection, tool_name: str, params: Dict[str, Any]
    ) -> str:
        """Call a tool via stdio transport."""
        import json

        if not conn.process or conn.process.poll() is not None:
            raise RuntimeError("MCP server process is not running")

        # Build the MCP request
        request_id = conn.get_next_request_id()
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params,
            },
        }

        # Send the request
        request_line = json.dumps(request) + "\n"

        async with conn._lock:
            conn.process.stdin.write(request_line)
            conn.process.stdin.flush()

        logger.debug(f"Sent MCP request: {request_line.strip()}")

        # Read response with timeout
        import select
        import time

        start_time = time.time()
        timeout = conn.config.timeout

        while time.time() - start_time < timeout:
            if conn.process.poll() is not None:
                stderr = conn.process.stderr.read() if conn.process.stderr else ""
                raise RuntimeError(f"MCP server process terminated. stderr: {stderr}")

            # Check if data is available
            if conn.process.stdout in select.select([conn.process.stdout], [], [], 0.1)[0]:
                response_line = conn.process.stdout.readline()
                if response_line:
                    try:
                        response = json.loads(response_line)
                        logger.debug(f"Received MCP response: {response}")

                        # Check if this is our response
                        if response.get("id") == request_id:
                            if "error" in response:
                                error = response["error"]
                                error_msg = error.get("message", str(error))
                                raise RuntimeError(f"MCP error: {error_msg}")

                            result = response.get("result", {})
                            content = result.get("content", [])

                            # Extract text content
                            texts = []
                            for item in content:
                                if item.get("type") == "text":
                                    texts.append(item.get("text", ""))
                                elif item.get("type") == "image":
                                    texts.append("[Image content]")
                                elif item.get("type") == "resource":
                                    resource = item.get("resource", {})
                                    texts.append(f"[Resource: {resource.get('uri', 'unknown')}]")

                            return "\n".join(texts) if texts else "Tool executed successfully (no text output)"
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse MCP response: {response_line}")

            await asyncio.sleep(0.01)

        raise TimeoutError(f"MCP tool call timed out after {timeout} seconds")

    async def close(self):
        """Close all MCP connections."""
        for server_name, conn in self.connections.items():
            try:
                if conn.process and conn.process.poll() is None:
                    # Try graceful shutdown first
                    try:
                        import json
                        shutdown_request = {
                            "jsonrpc": "2.0",
                            "id": conn.get_next_request_id(),
                            "method": "shutdown",
                        }
                        conn.process.stdin.write(json.dumps(shutdown_request) + "\n")
                        conn.process.stdin.flush()

                        # Wait for response
                        import select
                        start_time = time.time()
                        while time.time() - start_time < 5:
                            if select.select([conn.process.stdout], [], [], 0.1)[0]:
                                conn.process.stdout.readline()
                                break
                    except Exception as e:
                        logger.debug(f"Error during graceful shutdown: {e}")

                    # Terminate process
                    conn.process.terminate()
                    try:
                        conn.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        conn.process.kill()
                        conn.process.wait()

                    logger.debug(f"Closed MCP connection to {server_name}")
            except Exception as e:
                logger.error(f"Error closing MCP connection {server_name}: {e}")

        self.connections.clear()
        self._all_tools.clear()
        self._initialized = False
