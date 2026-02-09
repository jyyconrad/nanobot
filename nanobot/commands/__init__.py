"""Opencode commands system for Nanobot."""

from .registry import CommandRegistry

# Global command registry
_registry = None


def get_command_registry() -> CommandRegistry:
    """Get the global command registry instance."""
    global _registry
    if _registry is None:
        _registry = CommandRegistry()
    return _registry
