"""Tests for SubagentHooks component."""

from unittest.mock import MagicMock

import pytest

from nanobot.agent.subagent.agno_subagent import AgnoSubagentManager
from nanobot.agent.subagent.hooks import HookRegistration, HookType, SubagentHooks


@pytest.fixture
def mock_manager():
    """Create a mock AgnoSubagentManager."""
    manager = MagicMock(spec=AgnoSubagentManager)
    return manager


class TestHookType:
    """Tests for HookType model."""

    def test_hook_type_creation(self):
        """Test HookType initialization."""
        hook_type = HookType(
            name="pre_run", priority=1, description="Before subagent starts running"
        )

        assert hook_type.name == "pre_run"
        assert hook_type.priority == 1
        assert hook_type.description == "Before subagent starts running"

    def test_hook_type_comparison(self):
        """Test hook type comparison based on priority."""
        high_priority = HookType(name="pre_run", priority=1, description="High priority")
        low_priority = HookType(name="post_run", priority=10, description="Low priority")

        assert high_priority.priority < low_priority.priority


class TestHookRegistration:
    """Tests for HookRegistration model."""

    def test_hook_registration_creation(self):
        """Test HookRegistration initialization."""

        def callback(x):
            return x

        registration = HookRegistration(
            hook_type="pre_run", callback=callback, priority=5, enabled=True
        )

        assert registration.hook_type == "pre_run"
        assert registration.callback == callback
        assert registration.priority == 5
        assert registration.enabled is True


class TestSubagentHooks:
    """Tests for SubagentHooks component."""

    def test_initialization(self, mock_manager):
        """Test SubagentHooks initialization."""
        hooks = SubagentHooks(mock_manager)

        assert hooks.manager == mock_manager
        assert len(hooks._hooks) > 0
        assert len(hooks._hook_types) > 0

    def test_get_hook_types(self, mock_manager):
        """Test getting all hook types."""
        hooks = SubagentHooks(mock_manager)

        hook_types = hooks.get_hook_types()
        assert len(hook_types) > 0
        assert "pre_run" in hook_types
        assert "post_run" in hook_types
        assert "register_tools" in hook_types

    def test_get_hook_type_details(self, mock_manager):
        """Test getting hook type details."""
        hooks = SubagentHooks(mock_manager)

        pre_run = hooks.get_hook_type_details("pre_run")
        assert pre_run is not None
        assert pre_run.name == "pre_run"
        assert pre_run.priority == 1

        post_run = hooks.get_hook_type_details("post_run")
        assert post_run is not None
        assert post_run.name == "post_run"
        assert post_run.priority == 10

    @pytest.mark.asyncio
    async def test_register_and_unregister_hook(self, mock_manager):
        """Test registering and unregistering a hook."""
        hooks = SubagentHooks(mock_manager)

        def callback(x):
            return x

        initial_count = hooks.get_hook_count("pre_run")

        await hooks.register_hook("pre_run", callback)
        assert hooks.get_hook_count("pre_run") == initial_count + 1

        await hooks.unregister_hook("pre_run", callback)
        assert hooks.get_hook_count("pre_run") == initial_count

    @pytest.mark.asyncio
    async def test_register_invalid_hook_type(self, mock_manager):
        """Test registering an invalid hook type."""
        hooks = SubagentHooks(mock_manager)

        def callback(x):
            return x

        with pytest.raises(ValueError):
            await hooks.register_hook("invalid_type", callback)

    @pytest.mark.asyncio
    async def test_unregister_invalid_hook_type(self, mock_manager):
        """Test unregistering from an invalid hook type."""
        hooks = SubagentHooks(mock_manager)

        def callback(x):
            return x

        with pytest.raises(ValueError):
            await hooks.unregister_hook("invalid_type", callback)

    @pytest.mark.asyncio
    async def test_execute_hook(self, mock_manager):
        """Test executing a hook."""
        hooks = SubagentHooks(mock_manager)

        results = []

        async def test_callback(subagent_id, **kwargs):
            results.append(subagent_id)

        await hooks.register_hook("pre_run", test_callback)

        await hooks.execute_hook("pre_run", "test-1234")
        assert len(results) == 1
        assert results[0] == "test-1234"

    @pytest.mark.asyncio
    async def test_execute_hook_with_arguments(self, mock_manager):
        """Test executing a hook with arguments."""
        hooks = SubagentHooks(mock_manager)

        results = []

        async def test_callback(subagent_id, **kwargs):
            results.append(kwargs.get("data"))

        await hooks.register_hook("pre_run", test_callback)

        await hooks.execute_hook("pre_run", "test-1234", data="test value")
        assert len(results) == 1
        assert results[0] == "test value"

    @pytest.mark.asyncio
    async def test_priority_order(self, mock_manager):
        """Test hooks are executed in priority order."""
        hooks = SubagentHooks(mock_manager)

        results = []

        async def low_priority(subagent_id):
            results.append("low")

        async def high_priority(subagent_id):
            results.append("high")

        await hooks.register_hook("pre_run", low_priority, priority=10)
        await hooks.register_hook("pre_run", high_priority, priority=1)

        await hooks.execute_hook("pre_run", "test-1234")
        assert results == ["high", "low"]

    @pytest.mark.asyncio
    async def test_disable_and_enable_hook(self, mock_manager):
        """Test disabling and enabling a hook."""
        hooks = SubagentHooks(mock_manager)

        results = []

        async def test_callback(subagent_id):
            results.append(subagent_id)

        await hooks.register_hook("pre_run", test_callback)

        # Should execute when enabled
        await hooks.execute_hook("pre_run", "test-1234")
        assert len(results) == 1

        # Disable the hook
        await hooks.disable_hook("pre_run", test_callback)
        await hooks.execute_hook("pre_run", "test-5678")
        assert len(results) == 1

        # Enable the hook
        await hooks.enable_hook("pre_run", test_callback)
        await hooks.execute_hook("pre_run", "test-9012")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_clear_hooks(self, mock_manager):
        """Test clearing all hooks."""
        hooks = SubagentHooks(mock_manager)

        async def test_callback(subagent_id):
            pass

        await hooks.register_hook("pre_run", test_callback)
        await hooks.register_hook("post_run", test_callback)

        await hooks.clear_hooks()
        assert hooks.get_hook_count() == 0

    @pytest.mark.asyncio
    async def test_clear_hook_type(self, mock_manager):
        """Test clearing hooks of specific type."""
        hooks = SubagentHooks(mock_manager)

        async def test_callback(subagent_id):
            pass

        await hooks.register_hook("pre_run", test_callback)
        await hooks.register_hook("post_run", test_callback)

        await hooks.clear_hooks("pre_run")
        assert hooks.get_hook_count("pre_run") == 0
        assert hooks.get_hook_count("post_run") == 1

    @pytest.mark.asyncio
    async def test_list_hooks(self, mock_manager):
        """Test listing all hooks."""
        hooks = SubagentHooks(mock_manager)

        async def test_callback(subagent_id):
            pass

        await hooks.register_hook("pre_run", test_callback, priority=1)

        hook_list = await hooks.list_hooks()
        assert "pre_run" in hook_list
        assert len(hook_list["pre_run"]) == 1
        assert hook_list["pre_run"][0]["callback"] == "test_callback"
        assert hook_list["pre_run"][0]["priority"] == 1
        assert hook_list["pre_run"][0]["enabled"] is True

    @pytest.mark.asyncio
    async def test_convenience_methods(self, mock_manager):
        """Test convenience methods for common hooks."""
        hooks = SubagentHooks(mock_manager)

        await hooks.add_task_tracking_hook()
        assert hooks.get_hook_count("pre_iteration") >= 1

        await hooks.add_error_tracking_hook()
        assert hooks.get_hook_count("pre_fail") >= 1

        await hooks.add_completion_hook()
        assert hooks.get_hook_count("pre_complete") >= 1

        await hooks.add_tool_registration_hook()
        assert hooks.get_hook_count("register_tools") >= 1

    @pytest.mark.asyncio
    async def test_pre_run_hook(self, mock_manager):
        """Test pre_run hook convenience method."""
        hooks = SubagentHooks(mock_manager)

        results = []

        async def callback(subagent_id):
            results.append(subagent_id)

        await hooks.register_hook("pre_run", callback)
        await hooks.pre_run("test-1234")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_post_run_hook(self, mock_manager):
        """Test post_run hook convenience method."""
        hooks = SubagentHooks(mock_manager)

        results = []

        async def callback(subagent_id):
            results.append(subagent_id)

        await hooks.register_hook("post_run", callback)
        await hooks.post_run("test-1234")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_register_tools_hook(self, mock_manager):
        """Test register_tools hook convenience method."""
        hooks = SubagentHooks(mock_manager)

        results = []

        async def callback(subagent_id, tools=None):
            results.append(tools)

        await hooks.register_hook("register_tools", callback)
        await hooks.register_tools("test-1234")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_iteration_hooks(self, mock_manager):
        """Test iteration hooks."""
        hooks = SubagentHooks(mock_manager)

        results = []

        async def pre_callback(subagent_id, iteration):
            results.append(f"pre_{iteration}")

        async def post_callback(subagent_id, iteration):
            results.append(f"post_{iteration}")

        await hooks.register_hook("pre_iteration", pre_callback)
        await hooks.register_hook("post_iteration", post_callback)

        await hooks.pre_iteration("test-1234", 5)
        await hooks.post_iteration("test-1234", 5)

        assert "pre_5" in results
        assert "post_5" in results

    @pytest.mark.asyncio
    async def test_tool_call_hooks(self, mock_manager):
        """Test tool call hooks."""
        hooks = SubagentHooks(mock_manager)

        results = []

        async def pre_callback(subagent_id, tool_call):
            results.append(f"pre_{tool_call}")

        async def post_callback(subagent_id, tool_call, result):
            results.append(f"post_{tool_call}_{result}")

        await hooks.register_hook("pre_tool_call", pre_callback)
        await hooks.register_hook("post_tool_call", post_callback)

        await hooks.pre_tool_call("test-1234", "read_file")
        await hooks.post_tool_call("test-1234", "read_file", "content")

        assert "pre_read_file" in results
        assert "post_read_file_content" in results

    @pytest.mark.asyncio
    async def test_complete_hooks(self, mock_manager):
        """Test complete hooks."""
        hooks = SubagentHooks(mock_manager)

        results = []

        async def pre_callback(subagent_id, result):
            results.append(f"pre_{result}")

        async def post_callback(subagent_id, result):
            results.append(f"post_{result}")

        await hooks.register_hook("pre_complete", pre_callback)
        await hooks.register_hook("post_complete", post_callback)

        await hooks.pre_complete("test-1234", "Success")
        await hooks.post_complete("test-1234", "Success")

        assert "pre_Success" in results
        assert "post_Success" in results

    @pytest.mark.asyncio
    async def test_cancel_hooks(self, mock_manager):
        """Test cancel hooks."""
        hooks = SubagentHooks(mock_manager)

        results = []

        async def pre_callback(subagent_id):
            results.append("pre")

        async def post_callback(subagent_id):
            results.append("post")

        await hooks.register_hook("pre_cancel", pre_callback)
        await hooks.register_hook("post_cancel", post_callback)

        await hooks.pre_cancel("test-1234")
        await hooks.post_cancel("test-1234")

        assert "pre" in results
        assert "post" in results

    @pytest.mark.asyncio
    async def test_fail_hooks(self, mock_manager):
        """Test fail hooks."""
        hooks = SubagentHooks(mock_manager)

        results = []

        async def pre_callback(subagent_id, error):
            results.append(f"pre_{error}")

        async def post_callback(subagent_id, error):
            results.append(f"post_{error}")

        await hooks.register_hook("pre_fail", pre_callback)
        await hooks.register_hook("post_fail", post_callback)

        await hooks.pre_fail("test-1234", "Error message")
        await hooks.post_fail("test-1234", "Error message")

        assert "pre_Error message" in results
        assert "post_Error message" in results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
