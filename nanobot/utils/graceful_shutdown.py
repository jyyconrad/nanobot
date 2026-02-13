"""
优雅关闭系统
============

提供应用程序的优雅关闭功能，确保所有资源都能
正确释放和清理。

功能特点：
- 信号处理和优雅关闭
- 资源清理管理
- 关闭钩子函数
- 关闭状态跟踪
"""

import os
import sys
import signal
import time
import threading
from typing import List, Callable, Optional

from loguru import logger

from nanobot.monitor.structured_logger import get_structured_logger


class GracefulShutdownManager:
    """
    优雅关闭管理器

    负责处理应用程序的优雅关闭。
    """

    def __init__(self):
        self.logger = get_structured_logger()
        self._shutdown_requested = False
        self._shutdown_complete = False
        self._shutdown_timeout = 30  # 默认30秒超时
        self._shutdown_hooks: List[Callable[[], None]] = []
        self._shutdown_event = threading.Event()

        # 注册信号处理
        self._register_signal_handlers()

    def _register_signal_handlers(self):
        """
        注册信号处理函数
        """
        # 处理中断信号
        def handle_signal(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self.request_shutdown()

        # 注册常见的中断信号
        for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGHUP]:
            signal.signal(sig, handle_signal)

    def request_shutdown(self):
        """
        请求关闭应用程序
        """
        if self._shutdown_requested:
            return

        self._shutdown_requested = True
        self.logger.info("Shutdown requested")
        self._shutdown_event.set()

    def is_shutdown_requested(self) -> bool:
        """
        检查是否已请求关闭

        Returns:
            如果已请求关闭返回 True，否则返回 False
        """
        return self._shutdown_requested

    def set_shutdown_timeout(self, timeout: int):
        """
        设置关闭超时时间

        Args:
            timeout: 超时时间（秒）
        """
        self._shutdown_timeout = timeout
        self.logger.debug(f"Shutdown timeout set to {timeout} seconds")

    def add_shutdown_hook(self, hook: Callable[[], None]):
        """
        添加关闭钩子

        Args:
            hook: 关闭时调用的函数
        """
        self._shutdown_hooks.append(hook)

    def remove_shutdown_hook(self, hook: Callable[[], None]):
        """
        移除关闭钩子

        Args:
            hook: 要移除的钩子函数
        """
        if hook in self._shutdown_hooks:
            self._shutdown_hooks.remove(hook)

    def run_shutdown_hooks(self):
        """
        运行所有关闭钩子
        """
        self.logger.info(f"Running {len(self._shutdown_hooks)} shutdown hooks")
        for i, hook in enumerate(self._shutdown_hooks):
            try:
                self.logger.debug(f"Running shutdown hook {i + 1}")
                hook()
            except Exception as e:
                self.logger.error(f"Error running shutdown hook {i + 1}: {e}")

    def shutdown(self) -> bool:
        """
        执行优雅关闭

        Returns:
            如果成功关闭返回 True，超时返回 False
        """
        if self._shutdown_complete:
            return True

        self.request_shutdown()

        # 运行关闭钩子
        self.run_shutdown_hooks()

        # 等待所有资源清理
        start_time = time.time()
        while not self._is_all_resources_cleaned() and time.time() - start_time < self._shutdown_timeout:
            time.sleep(0.5)

        if time.time() - start_time >= self._shutdown_timeout:
            self.logger.error("Shutdown timed out")
            return False

        self._shutdown_complete = True
        self.logger.info("Shutdown completed successfully")

        return True

    def _is_all_resources_cleaned(self) -> bool:
        """
        检查是否所有资源都已清理（占位方法）

        Returns:
            默认为 True，子类可以根据需要覆盖
        """
        return True

    def wait_for_shutdown(self, timeout: Optional[float] = None):
        """
        等待关闭请求

        Args:
            timeout: 超时时间（秒）
        """
        if self._shutdown_event.wait(timeout=timeout):
            self.logger.info("Shutdown event received")

    def get_shutdown_status(self) -> dict:
        """
        获取关闭状态信息

        Returns:
            关闭状态信息字典
        """
        return {
            "shutdown_requested": self._shutdown_requested,
            "shutdown_complete": self._shutdown_complete,
            "shutdown_timeout": self._shutdown_timeout,
            "num_hooks": len(self._shutdown_hooks),
            "shutdown_event_set": self._shutdown_event.is_set(),
        }


# 全局优雅关闭管理器实例
_shutdown_manager_instance: Optional[GracefulShutdownManager] = None


def get_shutdown_manager() -> GracefulShutdownManager:
    """
    获取全局优雅关闭管理器实例

    Returns:
        GracefulShutdownManager 实例
    """
    global _shutdown_manager_instance
    if _shutdown_manager_instance is None:
        _shutdown_manager_instance = GracefulShutdownManager()
    return _shutdown_manager_instance


# 便捷方法
def request_shutdown():
    """
    便捷方法：请求关闭应用程序
    """
    get_shutdown_manager().request_shutdown()


def is_shutdown_requested() -> bool:
    """
    便捷方法：检查是否已请求关闭

    Returns:
        如果已请求关闭返回 True，否则返回 False
    """
    return get_shutdown_manager().is_shutdown_requested()


def wait_for_shutdown(timeout: Optional[float] = None):
    """
    便捷方法：等待关闭请求

    Args:
        timeout: 超时时间（秒）
    """
    get_shutdown_manager().wait_for_shutdown(timeout)


def shutdown():
    """
    便捷方法：执行优雅关闭

    Returns:
        如果成功关闭返回 True，超时返回 False
    """
    return get_shutdown_manager().shutdown()


def add_shutdown_hook(hook: Callable[[], None]):
    """
    便捷方法：添加关闭钩子

    Args:
        hook: 关闭时调用的函数
    """
    get_shutdown_manager().add_shutdown_hook(hook)


def remove_shutdown_hook(hook: Callable[[], None]):
    """
    便捷方法：移除关闭钩子

    Args:
        hook: 要移除的钩子函数
    """
    get_shutdown_manager().remove_shutdown_hook(hook)


def set_shutdown_timeout(timeout: int):
    """
    便捷方法：设置关闭超时时间

    Args:
        timeout: 超时时间（秒）
    """
    get_shutdown_manager().set_shutdown_timeout(timeout)


def get_shutdown_status() -> dict:
    """
    便捷方法：获取关闭状态信息

    Returns:
        关闭状态信息字典
    """
    return get_shutdown_manager().get_shutdown_status()
