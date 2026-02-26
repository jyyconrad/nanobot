"""Filesystem tools for agent operations."""

from pathlib import Path
from typing import Any, List, Optional

from loguru import logger

from nanobot.agent.tools.base import Tool


def _resolve_path(
    path: str, workspace: Path | None = None, allowed_dir: Path | None = None
) -> Path:
    """Resolve path against workspace (if relative) and enforce directory restriction."""
    p = Path(path).expanduser()
    if not p.is_absolute() and workspace:
        p = workspace / p
    resolved = p.resolve()
    if allowed_dir:
        try:
            resolved.relative_to(allowed_dir.resolve())
        except ValueError:
            raise PermissionError(f"Path {path} is outside allowed directory {allowed_dir}")
    return resolved


class ReadFileTool(Tool):
    """Tool to read file contents."""

    name = "read_file"
    description = "Reads contents of a file"

    def __init__(self, workspace: Path | None = None, allowed_dir: Path | None = None):
        self._workspace = workspace
        self._allowed_dir = allowed_dir

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"file_path": {"type": "string", "description": "Path to file to read"}},
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
            path = _resolve_path(file_path, self._workspace, self._allowed_dir)
            if not path.exists():
                return f"Error: File not found: {file_path}"
            if not path.is_file():
                return f"Error: Not a file: {file_path}"
            return path.read_text(encoding="utf-8")
        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return f"Error reading file: {e}"


class WriteFileTool(Tool):
    """Tool to write content to a file."""

    name = "write_file"
    description = "Write content to a file"

    def __init__(self, workspace: Path | None = None, allowed_dir: Path | None = None):
        self._workspace = workspace
        self._allowed_dir = allowed_dir

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
            path = _resolve_path(file_path, self._workspace, self._allowed_dir)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return f"File written successfully: {file_path}"
        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return f"Error writing file: {e}"


class ListDirTool(Tool):
    """Tool to list directory contents."""

    name = "list_dir"
    description = "List directory contents"

    def __init__(self, workspace: Path | None = None, allowed_dir: Path | None = None):
        self._workspace = workspace
        self._allowed_dir = allowed_dir

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
            path = _resolve_path(dir_path, self._workspace, self._allowed_dir)
            if not path.is_dir():
                return f"Error: {dir_path} is not a directory"

            items = []
            for item in path.iterdir():
                items.append(str(item))
            return "\n".join(items)
        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            logger.error(f"Error listing directory {dir_path}: {e}")
            return f"Error listing directory: {e}"
