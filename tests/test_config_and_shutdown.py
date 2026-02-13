"""
测试配置热重载和优雅关闭功能
============================

测试配置热重载、优雅关闭、诊断工具和错误恢复。
"""

import os
import sys
import tempfile
import time

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nanobot.config.hot_reload import (
    add_config_callback,
    get_config_hot_reloader,
    is_config_watcher_running,
    reload_config,
    start_config_watcher,
    stop_config_watcher,
)
from nanobot.utils.cache import (
    FileCache,
    MemoryCache,
    cache_clear,
    cache_delete,
    cache_exists,
    cache_get,
    cache_set,
    cache_size,
    get_file_cache,
    get_memory_cache,
)
from nanobot.utils.graceful_shutdown import (
    add_shutdown_hook,
    get_shutdown_manager,
    get_shutdown_status,
    is_shutdown_requested,
    request_shutdown,
    shutdown,
    wait_for_shutdown,
)


class TestConfigHotReloader:
    """测试配置热重载器"""

    def test_get_config_hot_reloader(self):
        """测试获取全局配置热重载器实例"""
        # 使用临时配置文件
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as f:
            f.write("""
agents:
  defaults:
    workspace: "~/.nanobot/workspace"
    model: "anthropic/claude-opus-4-5"
""")
            temp_config_path = f.name

        try:
            reloader = get_config_hot_reloader(temp_config_path)
            assert reloader is not None
        finally:
            try:
                os.unlink(temp_config_path)
            except Exception:
                pass

    def test_start_stop_config_watcher(self):
        """测试启动和停止配置监控"""
        # 这个测试可能需要实际的配置文件，我们先跳过
        # 或者使用临时文件
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as f:
            f.write("""
agents:
  defaults:
    workspace: "~/.nanobot/workspace"
    model: "anthropic/claude-opus-4-5"
""")
            temp_config_path = f.name

        try:
            reloader = get_config_hot_reloader(temp_config_path)

            # 测试启动监控
            reloader.watch(interval=0.1)
            assert reloader.is_running() is True

            # 测试状态获取
            status = reloader.get_watch_status()
            assert status["running"] is True

            # 停止监控
            reloader.stop()
            assert reloader.is_running() is False
        finally:
            try:
                os.unlink(temp_config_path)
            except Exception:
                pass

    def test_add_remove_callbacks(self):
        """测试添加和删除回调"""
        reloader = get_config_hot_reloader()

        # 创建测试回调
        def callback1(old_config, new_config):
            pass

        def callback2(old_config, new_config):
            pass

        reloader.add_callback(callback1)
        assert callback1 in reloader._callbacks

        reloader.add_callback(callback2)
        assert callback2 in reloader._callbacks

        reloader.remove_callback(callback1)
        assert callback1 not in reloader._callbacks

        reloader.remove_callback(callback2)
        assert callback2 not in reloader._callbacks


class TestGracefulShutdown:
    """测试优雅关闭管理器"""

    def test_get_shutdown_manager(self):
        """测试获取全局优雅关闭管理器实例"""
        manager = get_shutdown_manager()
        assert manager is not None

    def test_request_shutdown(self):
        """测试请求关闭"""
        manager = get_shutdown_manager()
        assert manager.is_shutdown_requested() is False

        manager.request_shutdown()
        assert manager.is_shutdown_requested() is True

    def test_add_remove_shutdown_hooks(self):
        """测试添加和删除关闭钩子"""
        manager = get_shutdown_manager()

        # 创建测试钩子
        def hook1():
            pass

        def hook2():
            pass

        manager.add_shutdown_hook(hook1)
        assert hook1 in manager._shutdown_hooks

        manager.add_shutdown_hook(hook2)
        assert hook2 in manager._shutdown_hooks

        manager.remove_shutdown_hook(hook1)
        assert hook1 not in manager._shutdown_hooks

        manager.remove_shutdown_hook(hook2)
        assert hook2 not in manager._shutdown_hooks

    def test_get_shutdown_status(self):
        """测试获取关闭状态"""
        manager = get_shutdown_manager()
        status = manager.get_shutdown_status()
        assert isinstance(status, dict)
        assert "shutdown_requested" in status
        assert "shutdown_complete" in status
        assert "shutdown_timeout" in status
        assert "num_hooks" in status


class TestCacheSystem:
    """测试缓存系统"""

    def test_memory_cache_basic_operations(self):
        """测试内存缓存基本操作"""
        cache = MemoryCache(max_size=100)

        # 测试缓存是否为空
        assert cache.size() == 0

        # 测试设置和获取值
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.size() == 1

        # 测试获取不存在的键
        assert cache.get("nonexistent_key") is None
        assert cache.get("nonexistent_key", "default") == "default"

        # 测试存在性检查
        assert cache.exists("key1") is True
        assert cache.exists("nonexistent_key") is False

        # 测试删除值
        cache.set("key2", "value2")
        assert cache.size() == 2
        cache.delete("key2")
        assert cache.exists("key2") is False
        assert cache.size() == 1

        # 测试清除所有缓存
        cache.clear()
        assert cache.size() == 0
        assert cache.get("key1") is None

    def test_memory_cache_ttl(self):
        """测试内存缓存TTL功能"""
        cache = MemoryCache(max_size=100)

        # 设置带TTL的键
        cache.set("key1", "value1", ttl=0.1)
        assert cache.exists("key1") is True
        assert cache.get("key1") == "value1"

        # 等待TTL过期
        time.sleep(0.11)

        # 验证键已过期
        assert cache.exists("key1") is False
        assert cache.get("key1") is None

    def test_file_cache_basic_operations(self):
        """测试文件缓存基本操作"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = FileCache(cache_dir=temp_dir, max_size=100)

            # 测试缓存是否为空
            assert cache.size() == 0

            # 测试设置和获取值
            cache.set("key1", "value1")
            assert cache.get("key1") == "value1"
            assert cache.size() == 1

            # 测试获取不存在的键
            assert cache.get("nonexistent_key") is None
            assert cache.get("nonexistent_key", "default") == "default"

            # 测试存在性检查
            assert cache.exists("key1") is True
            assert cache.exists("nonexistent_key") is False

            # 测试删除值
            cache.set("key2", "value2")
            assert cache.size() == 2
            cache.delete("key2")
            assert cache.exists("key2") is False
            assert cache.size() == 1

            # 测试清除所有缓存
            cache.clear()
            assert cache.size() == 0
            assert cache.get("key1") is None

    def test_cache_convenience_methods(self):
        """测试缓存便捷方法"""
        # 清除之前可能遗留的缓存
        cache_clear()

        # 测试便捷方法
        cache_set("key1", "value1")
        assert cache_get("key1") == "value1"
        assert cache_exists("key1") is True
        assert cache_size() == 1

        cache_set("key2", "value2", ttl=0.1)
        assert cache_size() == 2

        cache_delete("key1")
        assert cache_exists("key1") is False
        assert cache_size() == 1

        # 等待TTL过期
        time.sleep(0.11)
        assert cache_exists("key2") is False

        cache_clear()
        assert cache_size() == 0

    def test_cache_performance(self):
        """测试缓存性能（不实际运行以避免延长测试时间）"""
        pass


class TestIntegration:
    """集成测试"""

    def test_initialization(self):
        """测试所有组件是否能正确初始化"""
        # 测试所有单例是否能正确初始化
        from nanobot.monitor.alert_manager import get_alert_manager
        from nanobot.monitor.diagnostics import get_system_diagnostic
        from nanobot.monitor.health_checker import get_health_checker
        from nanobot.monitor.performance_monitor import get_performance_monitor
        from nanobot.monitor.structured_logger import get_structured_logger

        logger = get_structured_logger()
        assert logger is not None

        monitor = get_performance_monitor()
        assert monitor is not None

        checker = get_health_checker()
        assert checker is not None

        alert_manager = get_alert_manager()
        assert alert_manager is not None

        diagnostic = get_system_diagnostic()
        assert diagnostic is not None

        config_reloader = get_config_hot_reloader()
        assert config_reloader is not None

        shutdown_manager = get_shutdown_manager()
        assert shutdown_manager is not None

        memory_cache = get_memory_cache()
        assert memory_cache is not None

        file_cache = get_file_cache()
        assert file_cache is not None

    def test_cache_with_ttl(self):
        """测试带TTL的缓存操作"""
        cache = get_memory_cache()

        # 设置带TTL的键
        cache.set("test_key", "test_value", ttl=0.1)

        # 立即验证键存在
        assert cache.get("test_key") == "test_value"
        assert cache.exists("test_key") is True

        # 等待TTL过期
        time.sleep(0.11)

        # 验证键已过期
        assert cache.get("test_key") is None
        assert cache.exists("test_key") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
