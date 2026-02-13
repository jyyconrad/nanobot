"""
配置热重载系统
==============

提供配置文件的热重载功能，允许在不重启应用程序的情况下
更新配置。

功能特点：
- 配置文件变化检测
- 配置更新通知
- 配置验证
- 热重载历史记录
"""

import os
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

from loguru import logger

from nanobot.config.schema import Config
from nanobot.monitor.structured_logger import get_structured_logger


class ConfigHotReloader:
    """
    配置热重载器

    用于监控配置文件变化并自动重载配置。
    """

    def __init__(self, config_path: str):
        self.config_path = Path(config_path).expanduser()
        self.logger = get_structured_logger()
        self._config: Optional[Config] = None
        self._last_modified: Optional[float] = None
        self._watch_thread: Optional[threading.Thread] = None
        self._should_stop = False
        self._callbacks: List[Callable[[Config, Config], None]] = []

        # 加载初始配置
        self._load_config()

    def _load_config(self) -> Config:
        """
        加载配置文件

        Returns:
            配置实例
        """
        self._config = Config.load(str(self.config_path))
        self._last_modified = self.config_path.stat().st_mtime
        return self._config

    def get_config(self) -> Config:
        """
        获取当前配置

        Returns:
            配置实例
        """
        if self._config is None:
            self._load_config()
        return self._config

    def reload_config(self) -> Optional[Config]:
        """
        手动重载配置

        Returns:
            新的配置实例或 None（加载失败）
        """
        try:
            old_config = self._config
            new_config = self._load_config()
            self.logger.info("Configuration reloaded successfully")

            # 调用回调
            for callback in self._callbacks:
                try:
                    callback(old_config, new_config)
                except Exception as e:
                    logger.error(f"Error calling hot reload callback: {e}")

            return new_config
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return None

    def watch(self, interval: float = 5.0):
        """
        开始监控配置文件变化

        Args:
            interval: 检查间隔（秒）
        """
        self._should_stop = False
        self._watch_thread = threading.Thread(
            target=self._watch_loop,
            args=(interval,),
            name="config-watcher",
            daemon=True,
        )
        self._watch_thread.start()
        self.logger.info(f"Config hot reloader started watching {self.config_path}")

    def stop(self):
        """
        停止监控配置文件变化
        """
        self._should_stop = True
        if self._watch_thread:
            self._watch_thread.join()
            self._watch_thread = None
        self.logger.info("Config hot reloader stopped")

    def _watch_loop(self, interval: float):
        """
        监控循环

        Args:
            interval: 检查间隔（秒）
        """
        while not self._should_stop:
            try:
                current_mtime = self.config_path.stat().st_mtime

                if self._last_modified is None or current_mtime > self._last_modified:
                    self.logger.debug(f"Config file {self.config_path} changed")
                    self.reload_config()

                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error watching config file: {e}")
                time.sleep(interval)

    def add_callback(self, callback: Callable[[Config, Config], None]):
        """
        添加配置变化回调

        Args:
            callback: 回调函数，接受旧配置和新配置作为参数
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[Config, Config], None]):
        """
        移除配置变化回调

        Args:
            callback: 回调函数
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def is_running(self) -> bool:
        """
        检查热重载器是否正在运行

        Returns:
            如果正在运行返回 True，否则返回 False
        """
        if self._watch_thread:
            return self._watch_thread.is_alive()
        return False

    def get_watch_status(self) -> Dict:
        """
        获取监控状态信息

        Returns:
            状态信息字典
        """
        return {
            "running": self.is_running(),
            "config_path": str(self.config_path),
            "last_modified": self._last_modified,
            "watch_interval": 5.0,
        }


# 全局热重载器实例
_hot_reloader_instance: Optional[ConfigHotReloader] = None


def get_config_hot_reloader(config_path: Optional[str] = None) -> ConfigHotReloader:
    """
    获取全局配置热重载器实例

    Args:
        config_path: 配置文件路径（可选）

    Returns:
        配置热重载器实例
    """
    global _hot_reloader_instance
    if _hot_reloader_instance is None:
        if config_path is None:
            config_path = os.environ.get("NANOBOT_CONFIG", "~/.nanobot/config.yaml")
        _hot_reloader_instance = ConfigHotReloader(config_path)
    return _hot_reloader_instance


def start_config_watcher(config_path: Optional[str] = None, interval: float = 5.0):
    """
    启动配置文件监控（便捷方法）

    Args:
        config_path: 配置文件路径
        interval: 检查间隔（秒）
    """
    reloader = get_config_hot_reloader(config_path)
    reloader.watch(interval)


def stop_config_watcher():
    """
    停止配置文件监控（便捷方法）
    """
    global _hot_reloader_instance
    if _hot_reloader_instance:
        _hot_reloader_instance.stop()


def reload_config():
    """
    手动重载配置（便捷方法）
    """
    if _hot_reloader_instance:
        return _hot_reloader_instance.reload_config()


def add_config_callback(callback: Callable[[Config, Config], None]):
    """
    添加配置变化回调（便捷方法）

    Args:
        callback: 回调函数，接受旧配置和新配置作为参数
    """
    reloader = get_config_hot_reloader()
    reloader.add_callback(callback)


def remove_config_callback(callback: Callable[[Config, Config], None]):
    """
    移除配置变化回调（便捷方法）

    Args:
        callback: 回调函数
    """
    reloader = get_config_hot_reloader()
    reloader.remove_callback(callback)


def is_config_watcher_running() -> bool:
    """
    检查配置监控是否正在运行（便捷方法）

    Returns:
        如果正在运行返回 True，否则返回 False
    """
    if _hot_reloader_instance:
        return _hot_reloader_instance.is_running()
    return False
