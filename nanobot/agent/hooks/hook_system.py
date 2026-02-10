"""
HookSystem 类 - 提供灵活的钩子系统机制
用于在提示词系统的各个阶段提供扩展点
"""

import logging
from typing import Callable, Dict, List

logger = logging.getLogger(__name__)


class HookSystem:
    """
    钩子系统类 - 管理和触发各种钩子事件

    支持的钩子类型：
    - on_config_loaded - 配置文件加载完成
    - on_prompts_loaded - 所有提示词加载完成
    - on_layer_loaded - 单个提示词层加载完成
    - on_main_agent_prompt_built - MainAgent 提示词构建完成
    - on_subagent_prompt_built - Subagent 提示词构建完成
    - on_prompt_ready - 通用提示词构建完成
    - on_agent_initialized - Agent 初始化完成
    - on_agent_ready - Agent 准备好
    """

    def __init__(self):
        """初始化钩子系统"""
        self._hooks: Dict[str, List[Callable]] = {}
        logger.debug("HookSystem 初始化完成")

    def register(self, hook_name: str, callback: Callable) -> None:
        """
        注册一个钩子回调函数

        Args:
            hook_name: 钩子名称
            callback: 回调函数
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []

        if callback not in self._hooks[hook_name]:
            self._hooks[hook_name].append(callback)
            logger.debug(f"钩子 '{hook_name}' 注册成功: {callback.__name__}")

    def unregister(self, hook_name: str, callback: Callable) -> None:
        """
        注销一个钩子回调函数

        Args:
            hook_name: 钩子名称
            callback: 回调函数
        """
        if hook_name in self._hooks:
            try:
                self._hooks[hook_name].remove(callback)
                logger.debug(f"钩子 '{hook_name}' 注销成功: {callback.__name__}")
            except ValueError:
                logger.debug(f"钩子 '{hook_name}' 中未找到回调函数: {callback.__name__}")

    def trigger(self, hook_name: str, **kwargs) -> None:
        """
        触发指定名称的钩子

        Args:
            hook_name: 钩子名称
            **kwargs: 传递给钩子回调的参数
        """
        if hook_name not in self._hooks:
            logger.debug(f"钩子 '{hook_name}' 未找到，跳过触发")
            return

        logger.debug(f"触发钩子 '{hook_name}'，共 {len(self._hooks[hook_name])} 个回调")

        for callback in self._hooks[hook_name]:
            try:
                callback(**kwargs)
            except Exception as e:
                logger.error(
                    f"钩子 '{hook_name}' 的回调函数 '{callback.__name__}' 执行失败: {str(e)}",
                    exc_info=True
                )

    def get_hooks(self, hook_name: str) -> List[Callable]:
        """
        获取指定钩子名称的所有回调函数

        Args:
            hook_name: 钩子名称

        Returns:
            回调函数列表
        """
        return self._hooks.get(hook_name, [])
