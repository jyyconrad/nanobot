"""Tests for Phase 1 security fixes."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from nanobot.agent.tools.filesystem import ReadFileTool, WriteFileTool, ListDirTool, _resolve_path


class TestPathTraversal:
    """Test path traversal prevention."""

    def test_resolve_path_with_workspace(self, tmp_path):
        """Test path resolution against workspace."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        test_file = workspace / "test.txt"
        test_file.write_text("content")

        resolved = _resolve_path("test.txt", workspace, workspace)
        assert resolved == test_file

    def test_resolve_path_blocks_traversal_outside_workspace(self, tmp_path):
        """Test that paths outside workspace are blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("secret")

        with pytest.raises(PermissionError) as exc_info:
            _resolve_path(str(outside_file), workspace, workspace)

        assert "outside allowed directory" in str(exc_info.value)

    def test_resolve_path_blocks_dotdot_traversal(self, tmp_path):
        """Test that ../ sequences are blocked."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        subdir = workspace / "subdir"
        subdir.mkdir()

        with pytest.raises(PermissionError):
            _resolve_path("../../../etc/passwd", workspace, workspace)

    def test_resolve_path_allows_valid_subdir_access(self, tmp_path):
        """Test that valid subdirectory access is allowed."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        subdir = workspace / "subdir"
        subdir.mkdir()

        resolved = _resolve_path("subdir", workspace, workspace)
        assert resolved == subdir


class TestReadFileTool:
    """Test ReadFileTool security."""

    async def test_read_file_within_allowed_dir(self, tmp_path):
        """Test reading file within allowed directory."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        test_file = workspace / "test.txt"
        test_file.write_text("test content")

        tool = ReadFileTool(workspace=workspace, allowed_dir=workspace)
        result = await tool.execute(file_path="test.txt")

        assert "test content" in result

    async def test_read_file_blocks_traversal(self, tmp_path):
        """Test that read_file blocks path traversal."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("secret")

        tool = ReadFileTool(workspace=workspace, allowed_dir=workspace)
        result = await tool.execute(file_path=str(outside_file))

        assert "outside allowed directory" in result or "Error" in result


class TestWriteFileTool:
    """Test WriteFileTool security."""

    async def test_write_file_within_allowed_dir(self, tmp_path):
        """Test writing file within allowed directory."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        tool = WriteFileTool(workspace=workspace, allowed_dir=workspace)
        result = await tool.execute(file_path="test.txt", content="test content")

        assert "File written successfully" in result
        assert (workspace / "test.txt").exists()

    async def test_write_file_blocks_traversal(self, tmp_path):
        """Test that write_file blocks path traversal."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        tool = WriteFileTool(workspace=workspace, allowed_dir=workspace)
        result = await tool.execute(file_path="../../../tmp/evil.txt", content="evil")

        assert "outside allowed directory" in result or "Error" in result


class TestAPIKeyHotReload:
    """Test API key hot-reload functionality."""

    def test_api_key_property_priority(self):
        """Test that environment variable takes priority."""
        from nanobot.providers.litellm_provider import LiteLLMProvider

        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            provider = LiteLLMProvider(api_key="config-key", default_model="openai/gpt-4")

            # Property should return env var value
            assert provider.api_key == "env-key"

    def test_api_key_fallback_to_config(self):
        """Test fallback to config value when no env var."""
        from nanobot.providers.litellm_provider import LiteLLMProvider

        # Ensure no env var is set
        with patch.dict(os.environ, {}, clear=True):
            provider = LiteLLMProvider(api_key="config-key", default_model="openai/gpt-4")

            assert provider.api_key == "config-key"

    def test_api_key_change_without_restart(self):
        """Test that API key changes take effect without restart."""
        from nanobot.providers.litellm_provider import LiteLLMProvider

        with patch.dict(os.environ, {"OPENAI_API_KEY": "key-1"}, clear=True):
            provider = LiteLLMProvider(api_key="key-1", default_model="openai/gpt-4")
            assert provider.api_key == "key-1"

            # Change env var
            os.environ["OPENAI_API_KEY"] = "key-2"

            # Should reflect new value without restart
            assert provider.api_key == "key-2"

    def test_openrouter_api_key_hot_reload(self):
        """Test OpenRouter API key hot-reload."""
        from nanobot.providers.litellm_provider import LiteLLMProvider

        # Clear any existing OPENROUTER_API_KEY first
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "or-key-1"}, clear=False):
            # Store original value if exists
            original_key = os.environ.get("OPENROUTER_API_KEY")
            try:
                os.environ["OPENROUTER_API_KEY"] = "or-key-1"
                provider = LiteLLMProvider(
                    api_key="or-key-1", default_model="openrouter/anthropic/claude-3"
                )
                assert provider.api_key == "or-key-1"

                # Change env var
                os.environ["OPENROUTER_API_KEY"] = "or-key-2"

                assert provider.api_key == "or-key-2"
            finally:
                # Restore original value
                if original_key:
                    os.environ["OPENROUTER_API_KEY"] = original_key


class TestSecurityIntegration:
    """Integration tests for security features."""

    async def test_filesystem_tools_with_real_workspace(self, tmp_path):
        """Test filesystem tools with real workspace setup."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Create test structure
        (workspace / "subdir").mkdir()
        (workspace / "file.txt").write_text("test")
        (workspace / "subdir" / "nested.txt").write_text("nested")

        # Test read
        read_tool = ReadFileTool(workspace=workspace, allowed_dir=workspace)
        result = await read_tool.execute(file_path="file.txt")
        assert "test" in result

        # Test nested read
        result = await read_tool.execute(file_path="subdir/nested.txt")
        assert "nested" in result

        # Test write
        write_tool = WriteFileTool(workspace=workspace, allowed_dir=workspace)
        result = await write_tool.execute(file_path="new.txt", content="new content")
        assert "success" in result.lower()
        assert (workspace / "new.txt").exists()

        # Test list
        list_tool = ListDirTool(workspace=workspace, allowed_dir=workspace)
        result = await list_tool.execute(dir_path=".")
        assert "file.txt" in result
        assert "subdir" in result
