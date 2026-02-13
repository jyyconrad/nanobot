"""
Hooks 系统 - 提供提示词系统的扩展点机制
"""

# 直接从 hooks.py 文件导入类
import sys
from pathlib import Path

from .hook_system import HookSystem

# 确保我们可以导入 hooks.py 文件
hooks_py_path = Path(__file__).parent.parent / "hooks.py"
if hooks_py_path.exists():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "nanobot.agent.hooks_module", str(hooks_py_path)
    )
    hooks_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hooks_module)

    # 将需要的类添加到当前命名空间
    if hasattr(hooks_module, "HookResult"):
        HookResult = hooks_module.HookResult
    if hasattr(hooks_module, "MainAgentHooks"):
        MainAgentHooks = hooks_module.MainAgentHooks
    if hasattr(hooks_module, "LoggingHooksDecorator"):
        LoggingHooksDecorator = hooks_module.LoggingHooksDecorator
    if hasattr(hooks_module, "MetricsHooksDecorator"):
        MetricsHooksDecorator = hooks_module.MetricsHooksDecorator

__all__ = [
    "HookSystem",
    "HookResult",
    "LoggingHooksDecorator",
    "MainAgentHooks",
    "MetricsHooksDecorator",
]
