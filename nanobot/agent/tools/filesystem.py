"""Filesystem tools for agent operations."""

from pathlib import Path
from typing import Any, List, Optional

from loguru import logger

from nanobot.agent.tools.base import Tool


class ReadFileTool(Tool):
    """Tool to read file contents."""

    name = "read_file"
    description = "Reads contents of a file"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to file to read"}
            },
            "required": ["file_path"],
        }

    async def execute(self, file_path: str, **kwargs) -> str:
        """Read file contents.

        Args:
            file_path: Path to file to read

        Returns:
            File contents as string
        """
        try:
            path = Path(file_path)
            return path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return f"Error reading file: {e}"


class WriteFileTool(Tool):
    """Tool to write content to a file."""

    name = "write_file"
    description = "Write content to a file"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to file to write"},
                "content": {
                    "type": "string",
                    "description": "Content to write to file",
                },
            },
            "required": ["file_path", "content"],
        }

    async def execute(self, file_path: str, content: str, **kwargs) -> str:
        """Write content to a file.

        Args:
            file_path: Path to file to write
            content: Content to write to file

        Returns:
            Success message
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return f"File written successfully: {file_path}"
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return f"Error writing file: {e}"


class ListDirTool(Tool):
    """Tool to list directory contents."""

    name = "list_dir"
    description = "List directory contents"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "dir_path": {
                    "type": "string",
                    "description": "Path to directory to list",
                }
            },
            "required": ["dir_path"],
        }

    async def execute(self, dir_path: str, **kwargs) -> str:
        """List directory contents.

        Args:
            dir_path: Path to directory to list

        Returns:
            List of files and directories
        """
        try:
            path = Path(dir_path)
            if not path.is_dir():
                return f"Error: {dir_path} is not a directory"

            items = []
            for item in path.iterdir():
                items.append(str(item))
            return "\n".join(items)
        except Exception as e:
            logger.error(f"Error listing directory {dir_path}: {e}")
            return f"Error listing directory: {e}"
