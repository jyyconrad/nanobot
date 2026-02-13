"""Subagent session hooks for customization and extensibility."""

import asyncio
from typing import Any, Callable, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from nanobot.agent.subagent.agno_subagent import AgnoSubagentManager
from nanobot.agent.tools.registry import ToolRegistry


class HookType(BaseModel):
    """Hook type classification model."""

    name: str = Field(..., description="Hook name")
    priority: int = Field(default=5, description="Hook priority (1-10)")
    description: str = Field(default="", description="Hook description")


class HookRegistration(BaseModel):
    """Hook registration model."""

    hook_type: str = Field(..., description="Type of hook")
    callback: Callable = Field(..., description="Callback function to execute")
    priority: int = Field(default=5, description="Hook priority (1-10)")
    enabled: bool = Field(default=True, description="Whether the hook is enabled")


class SubagentHooks:
    """
    Subagent session hooks for customization and extensibility.

    This component provides a hook system for extending subagent behavior at
    various points in the subagent lifecycle.
    """

    def __init__(self, manager: AgnoSubagentManager):
        self.manager = manager
        self._hooks: Dict[str, List[HookRegistration]] = {
            "pre_run": [],
            "post_run": [],
            "register_tools": [],
            "pre_iteration": [],
            "post_iteration": [],
            "pre_tool_call": [],
            "post_tool_call": [],
            "pre_complete": [],
            "post_complete": [],
            "pre_cancel": [],
            "post_cancel": [],
            "pre_fail": [],
            "post_fail": [],
        }

        self._hook_types: Dict[str, HookType] = {
            "pre_run": HookType(
                name="pre_run", priority=1, description="Before subagent starts running"
            ),
            "post_run": HookType(
                name="post_run", priority=10, description="After subagent completes"
            ),
            "register_tools": HookType(
                name="register_tools",
                priority=2,
                description="When tools are being registered",
            ),
            "pre_iteration": HookType(
                name="pre_iteration", priority=3, description="Before each iteration"
            ),
            "post_iteration": HookType(
                name="post_iteration", priority=9, description="After each iteration"
            ),
            "pre_tool_call": HookType(
                name="pre_tool_call",
                priority=4,
                description="Before executing tool calls",
            ),
            "post_tool_call": HookType(
                name="post_tool_call",
                priority=8,
                description="After executing tool calls",
            ),
            "pre_complete": HookType(
                name="pre_complete",
                priority=5,
                description="Before completing the task",
            ),
            "post_complete": HookType(
                name="post_complete", priority=11, description="After task is completed"
            ),
            "pre_cancel": HookType(
                name="pre_cancel", priority=6, description="Before task is cancelled"
            ),
            "post_cancel": HookType(
                name="post_cancel", priority=12, description="After task is cancelled"
            ),
            "pre_fail": HookType(
                name="pre_fail", priority=7, description="Before task fails"
            ),
            "post_fail": HookType(
                name="post_fail", priority=13, description="After task fails"
            ),
        }

    async def register_hook(
        self,
        hook_type: str,
        callback: Callable,
        priority: int = 5,
        enabled: bool = True,
    ) -> None:
        """
        Register a new hook callback.

        Args:
            hook_type: Type of hook to register for
            callback: Callback function to execute
            priority: Hook priority (lower numbers run first)
            enabled: Whether the hook is enabled

        Raises:
            ValueError: If hook_type is not valid
        """
        if hook_type not in self._hooks:
            raise ValueError(f"Invalid hook type: {hook_type}")

        self._hooks[hook_type].append(
            HookRegistration(
                hook_type=hook_type,
                callback=callback,
                priority=priority,
                enabled=enabled,
            )
        )

        # Sort hooks by priority
        self._hooks[hook_type].sort(key=lambda x: x.priority)

        logger.debug(f"Registered hook {hook_type} with callback {callback.__name__}")

    async def unregister_hook(self, hook_type: str, callback: Callable) -> None:
        """
        Unregister a hook callback.

        Args:
            hook_type: Type of hook to unregister from
            callback: Callback function to remove

        Raises:
            ValueError: If hook_type is not valid
        """
        if hook_type not in self._hooks:
            raise ValueError(f"Invalid hook type: {hook_type}")

        self._hooks[hook_type] = [
            h for h in self._hooks[hook_type] if h.callback != callback
        ]

        logger.debug(f"Unregistered hook {hook_type} with callback {callback.__name__}")

    async def execute_hook(
        self, hook_type: str, subagent_id: str, **kwargs
    ) -> List[Any]:
        """
        Execute all registered hooks for a specific hook type.

        Args:
            hook_type: Type of hook to execute
            subagent_id: Subagent ID
            **kwargs: Additional arguments to pass to hooks

        Returns:
            List of results from each hook call

        Raises:
            ValueError: If hook_type is not valid
        """
        if hook_type not in self._hooks:
            raise ValueError(f"Invalid hook type: {hook_type}")

        results = []
        for registration in self._hooks[hook_type]:
            if registration.enabled:
                try:
                    logger.debug(
                        f"Executing hook {hook_type} with callback {registration.callback.__name__}"
                    )
                    result = await self._call_callback(
                        registration.callback, subagent_id, **kwargs
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Hook {hook_type} failed: {e}")

        return results

    async def _call_callback(
        self, callback: Callable, subagent_id: str, **kwargs
    ) -> Any:
        """Call a single hook callback."""
        if asyncio.iscoroutinefunction(callback):
            return await callback(subagent_id, **kwargs)
        else:
            return callback(subagent_id, **kwargs)

    # Convenience methods for common hook types
    async def pre_run(self, subagent_id: str, **kwargs) -> List[Any]:
        """Execute pre_run hooks."""
        return await self.execute_hook("pre_run", subagent_id, **kwargs)

    async def post_run(self, subagent_id: str, **kwargs) -> List[Any]:
        """Execute post_run hooks."""
        return await self.execute_hook("post_run", subagent_id, **kwargs)

    async def register_tools(self, tools: ToolRegistry, **kwargs) -> List[Any]:
        """Execute register_tools hooks."""
        return await self.execute_hook(
            "register_tools", "tools_registration", tools=tools, **kwargs
        )

    async def pre_iteration(
        self, subagent_id: str, iteration: int, **kwargs
    ) -> List[Any]:
        """Execute pre_iteration hooks."""
        return await self.execute_hook(
            "pre_iteration", subagent_id, iteration=iteration, **kwargs
        )

    async def post_iteration(
        self, subagent_id: str, iteration: int, **kwargs
    ) -> List[Any]:
        """Execute post_iteration hooks."""
        return await self.execute_hook(
            "post_iteration", subagent_id, iteration=iteration, **kwargs
        )

    async def pre_tool_call(
        self, subagent_id: str, tool_call: Any, **kwargs
    ) -> List[Any]:
        """Execute pre_tool_call hooks."""
        return await self.execute_hook(
            "pre_tool_call", subagent_id, tool_call=tool_call, **kwargs
        )

    async def post_tool_call(
        self, subagent_id: str, tool_call: Any, result: Any, **kwargs
    ) -> List[Any]:
        """Execute post_tool_call hooks."""
        return await self.execute_hook(
            "post_tool_call", subagent_id, tool_call=tool_call, result=result, **kwargs
        )

    async def pre_complete(self, subagent_id: str, result: str, **kwargs) -> List[Any]:
        """Execute pre_complete hooks."""
        return await self.execute_hook(
            "pre_complete", subagent_id, result=result, **kwargs
        )

    async def post_complete(self, subagent_id: str, result: str, **kwargs) -> List[Any]:
        """Execute post_complete hooks."""
        return await self.execute_hook(
            "post_complete", subagent_id, result=result, **kwargs
        )

    async def pre_cancel(self, subagent_id: str, **kwargs) -> List[Any]:
        """Execute pre_cancel hooks."""
        return await self.execute_hook("pre_cancel", subagent_id, **kwargs)

    async def post_cancel(self, subagent_id: str, **kwargs) -> List[Any]:
        """Execute post_cancel hooks."""
        return await self.execute_hook("post_cancel", subagent_id, **kwargs)

    async def pre_fail(self, subagent_id: str, error: str, **kwargs) -> List[Any]:
        """Execute pre_fail hooks."""
        return await self.execute_hook("pre_fail", subagent_id, error=error, **kwargs)

    async def post_fail(self, subagent_id: str, error: str, **kwargs) -> List[Any]:
        """Execute post_fail hooks."""
        return await self.execute_hook("post_fail", subagent_id, error=error, **kwargs)

    def get_hook_count(self, hook_type: str = None) -> int:
        """
        Get the number of registered hooks.

        Args:
            hook_type: Optional hook type to count

        Returns:
            Total number of registered hooks
        """
        if hook_type:
            if hook_type not in self._hooks:
                raise ValueError(f"Invalid hook type: {hook_type}")
            return len(self._hooks[hook_type])

        total = 0
        for hooks in self._hooks.values():
            total += len(hooks)
        return total

    def get_hook_types(self) -> List[str]:
        """Get all available hook types."""
        return list(self._hooks.keys())

    def get_hook_type_details(self, hook_type: str) -> Optional[HookType]:
        """Get details about a specific hook type."""
        return self._hook_types.get(hook_type)

    async def enable_hook(self, hook_type: str, callback: Callable) -> None:
        """
        Enable a hook callback.

        Args:
            hook_type: Type of hook
            callback: Callback function to enable

        Raises:
            ValueError: If hook_type is not valid
        """
        if hook_type not in self._hooks:
            raise ValueError(f"Invalid hook type: {hook_type}")

        for registration in self._hooks[hook_type]:
            if registration.callback == callback:
                registration.enabled = True
                logger.debug(
                    f"Enabled hook {hook_type} with callback {callback.__name__}"
                )

    async def disable_hook(self, hook_type: str, callback: Callable) -> None:
        """
        Disable a hook callback.

        Args:
            hook_type: Type of hook
            callback: Callback function to disable

        Raises:
            ValueError: If hook_type is not valid
        """
        if hook_type not in self._hooks:
            raise ValueError(f"Invalid hook type: {hook_type}")

        for registration in self._hooks[hook_type]:
            if registration.callback == callback:
                registration.enabled = False
                logger.debug(
                    f"Disabled hook {hook_type} with callback {callback.__name__}"
                )

    async def clear_hooks(self, hook_type: str = None) -> None:
        """
        Clear all registered hooks.

        Args:
            hook_type: Optional hook type to clear

        Raises:
            ValueError: If hook_type is not valid
        """
        if hook_type:
            if hook_type not in self._hooks:
                raise ValueError(f"Invalid hook type: {hook_type}")
            self._hooks[hook_type].clear()
            logger.debug(f"Cleared all hooks for type: {hook_type}")
        else:
            for hook_type in self._hooks:
                self._hooks[hook_type].clear()
            logger.debug("Cleared all hooks")

    async def list_hooks(self) -> Dict[str, List[str]]:
        """List all registered hooks with callback names."""
        hook_list = {}
        for hook_type, registrations in self._hooks.items():
            hook_list[hook_type] = []
            for registration in registrations:
                hook_list[hook_type].append(
                    {
                        "callback": registration.callback.__name__,
                        "priority": registration.priority,
                        "enabled": registration.enabled,
                    }
                )

        return hook_list

    # Helper methods for common use cases
    async def add_task_tracking_hook(self):
        """Add a hook for tracking task progress."""

        async def track_task_progress(subagent_id: str, iteration: int = 0):
            subagent = self.manager.get_subagent_by_id(subagent_id)
            if subagent:
                logger.debug(
                    f"Task progress: Subagent [{subagent_id}] "
                    f"Iteration {iteration} "
                    f"Progress: {subagent.progress:.1f}%"
                )

        await self.register_hook("pre_iteration", track_task_progress, priority=1)

    async def add_error_tracking_hook(self):
        """Add a hook for tracking errors."""

        async def track_error(subagent_id: str, error: str):
            logger.error(f"Subagent [{subagent_id}] failed: {error}")

        await self.register_hook("pre_fail", track_error, priority=1)

    async def add_completion_hook(self):
        """Add a hook for tracking completion."""

        async def track_completion(subagent_id: str, result: str):
            logger.info(
                f"Subagent [{subagent_id}] completed with result: {result[:100]}..."
            )

        await self.register_hook("pre_complete", track_completion, priority=1)

    async def add_tool_registration_hook(self):
        """Add a hook for custom tool registration."""

        async def custom_tool_registration(subagent_id: str, tools: ToolRegistry):
            logger.debug(f"Registering custom tools for subagent [{subagent_id}]")
            # Example: Add custom tool here
            # from mytools import CustomTool
            # tools.register(CustomTool())

        await self.register_hook("register_tools", custom_tool_registration, priority=1)
