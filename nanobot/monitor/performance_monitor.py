"""
性能监控系统
============

提供应用程序性能监控功能，包括资源使用情况、响应时间、
并发连接数等指标的收集和报告。

功能特点：
- CPU 和内存使用监控
- 系统资源监控
- 响应时间测量
- 并发连接数统计
- 性能指标报告
"""

import time
import resource
from datetime import datetime
from typing import Dict, Optional, Any, Callable

from loguru import logger

from nanobot.monitor.structured_logger import get_structured_logger


class PerformanceMonitor:
    """
    性能监控器

    用于收集和报告应用程序的性能指标。
    """

    def __init__(self):
        self.logger = get_structured_logger()
        self._start_time = time.time()
        self._last_check_time = time.time()
        self._metrics: Dict[str, Any] = {}
        self._performance_history: Dict[str, list] = {}

    def get_memory_usage(self) -> float:
        """
        获取当前内存使用量（MB）

        Returns:
            内存使用量（MB）
        """
        try:
            # 获取当前进程的内存使用（KB）
            mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

            # 转换为 MB（macOS 以字节为单位，其他系统以 KB 为单位）
            if sys.platform == "darwin":
                return mem_usage / (1024 * 1024)
            return mem_usage / 1024
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return 0.0

    def get_cpu_usage(self) -> float:
        """
        获取 CPU 使用率

        Returns:
            CPU 使用率（百分比）
        """
        try:
            import psutil

            return psutil.cpu_percent()
        except ImportError:
            logger.warning("psutil module not available, CPU usage monitoring disabled")
            return 0.0
        except Exception as e:
            logger.error(f"Failed to get CPU usage: {e}")
            return 0.0

    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息

        Returns:
            包含系统信息的字典
        """
        info = {
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time() - self._start_time,
            "memory_usage": self.get_memory_usage(),
            "cpu_usage": self.get_cpu_usage(),
        }

        try:
            import psutil

            # 获取系统内存信息
            vm = psutil.virtual_memory()
            info["system_memory_total"] = vm.total / (1024 * 1024)  # MB
            info["system_memory_available"] = vm.available / (1024 * 1024)  # MB
            info["system_memory_used"] = vm.used / (1024 * 1024)  # MB
            info["system_memory_percent"] = vm.percent

            # 获取磁盘使用情况
            disk = psutil.disk_usage("/")
            info["disk_total"] = disk.total / (1024 * 1024 * 1024)  # GB
            info["disk_used"] = disk.used / (1024 * 1024 * 1024)  # GB
            info["disk_free"] = disk.free / (1024 * 1024 * 1024)  # GB
            info["disk_percent"] = disk.percent
        except ImportError:
            logger.warning("psutil module not available, system info limited")
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")

        return info

    def measure_time(self, operation: str) -> Callable:
        """
        装饰器：测量函数执行时间

        Args:
            operation: 操作名称

        Returns:
            装饰器函数
        """

        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.logger.log_performance(operation, duration)

                    # 记录到历史
                    if operation not in self._performance_history:
                        self._performance_history[operation] = []
                    self._performance_history[operation].append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "duration": duration,
                            "status": "success",
                        }
                    )
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.logger.log_performance(operation, duration, status="failed")

                    if operation not in self._performance_history:
                        self._performance_history[operation] = []
                    self._performance_history[operation].append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "duration": duration,
                            "status": "failed",
                            "error": str(e),
                        }
                    )
                    raise e

            return wrapper

        return decorator

    class Timer:
        """
        上下文管理器：测量代码块执行时间
        """

        def __init__(self, monitor: "PerformanceMonitor", operation: str):
            self.monitor = monitor
            self.operation = operation
            self.start_time = 0.0

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            status = "failed" if exc_type else "success"
            self.monitor.logger.log_performance(self.operation, duration, status)

            if self.operation not in self.monitor._performance_history:
                self.monitor._performance_history[self.operation] = []
            self.monitor._performance_history[self.operation].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "duration": duration,
                    "status": status,
                    "error": str(exc_val) if exc_val else None,
                }
            )

    def timer(self, operation: str) -> Timer:
        """
        创建一个计时器上下文管理器

        Args:
            operation: 操作名称

        Returns:
            计时器上下文管理器
        """
        return self.Timer(self, operation)

    def record_response_time(self, endpoint: str, duration: float, status_code: int = 200):
        """
        记录 API 响应时间

        Args:
            endpoint: API 端点
            duration: 响应时间（秒）
            status_code: HTTP 状态码
        """
        status = "success" if status_code < 400 else "error"
        self.logger.log_performance(
            f"API:{endpoint}",
            duration,
            status=status,
            endpoint=endpoint,
            status_code=status_code,
        )

        # 记录到历史
        metric_name = f"api.response_time.{endpoint}"
        if metric_name not in self._performance_history:
            self._performance_history[metric_name] = []
        self._performance_history[metric_name].append(
            {
                "timestamp": datetime.now().isoformat(),
                "duration": duration,
                "status_code": status_code,
                "status": status,
            }
        )

    def record_concurrent_connections(self, count: int, service: str = "default"):
        """
        记录并发连接数

        Args:
            count: 并发连接数
            service: 服务名称
        """
        self.logger.log_metric(f"concurrent_connections.{service}", count)

        # 记录到历史
        metric_name = f"concurrent_connections.{service}"
        if metric_name not in self._performance_history:
            self._performance_history[metric_name] = []
        self._performance_history[metric_name].append(
            {
                "timestamp": datetime.now().isoformat(),
                "value": count,
            }
        )

    def record_queue_size(self, queue_name: str, size: int):
        """
        记录队列大小

        Args:
            queue_name: 队列名称
            size: 队列大小
        """
        self.logger.log_metric(f"queue.size.{queue_name}", size)

        # 记录到历史
        metric_name = f"queue.size.{queue_name}"
        if metric_name not in self._performance_history:
            self._performance_history[metric_name] = []
        self._performance_history[metric_name].append(
            {
                "timestamp": datetime.now().isoformat(),
                "value": size,
            }
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要

        Returns:
            性能摘要字典
        """
        summary = self.get_system_info()

        # 计算平均响应时间
        for operation, history in self._performance_history.items():
            if operation.startswith("API:") or operation in [
                "task_execution",
                "message_processing",
            ]:
                durations = [
                    entry["duration"] for entry in history if entry.get("status") == "success"
                ]
                if durations:
                    avg_duration = sum(durations) / len(durations)
                    summary[f"{operation}.avg_response_time"] = avg_duration
                    summary[f"{operation}.total_requests"] = len(history)

        return summary

    def get_performance_history(self, metric: str, limit: int = 100) -> list:
        """
        获取指标的历史记录

        Args:
            metric: 指标名称
            limit: 返回记录的最大数量

        Returns:
            指标历史记录
        """
        return self._performance_history.get(metric, [])[-limit:]

    def check_performance_thresholds(self, thresholds: Dict[str, Any]) -> list:
        """
        检查性能阈值是否超过

        Args:
            thresholds: 性能阈值配置

        Returns:
            超过阈值的告警列表
        """
        alerts = []
        system_info = self.get_system_info()

        # 检查内存使用
        if "memory_threshold" in thresholds:
            if system_info["memory_usage"] > thresholds["memory_threshold"]:
                alerts.append(
                    {
                        "type": "memory",
                        "severity": "warning" if system_info["memory_usage"] < thresholds.get(
                            "memory_critical_threshold", 90
                        ) else "critical",
                        "message": f"Memory usage {system_info['memory_usage']:.1f}% exceeds threshold {thresholds['memory_threshold']}%",
                        "value": system_info["memory_usage"],
                    }
                )

        # 检查 CPU 使用
        if "cpu_threshold" in thresholds:
            if system_info["cpu_usage"] > thresholds["cpu_threshold"]:
                alerts.append(
                    {
                        "type": "cpu",
                        "severity": "warning" if system_info["cpu_usage"] < thresholds.get(
                            "cpu_critical_threshold", 95
                        ) else "critical",
                        "message": f"CPU usage {system_info['cpu_usage']:.1f}% exceeds threshold {thresholds['cpu_threshold']}%",
                        "value": system_info["cpu_usage"],
                    }
                )

        # 检查响应时间
        for operation, history in self._performance_history.items():
            if operation.startswith("API:") or operation in [
                "task_execution",
                "message_processing",
            ]:
                if f"{operation}_response_threshold" in thresholds:
                    durations = [
                        entry["duration"] for entry in history if entry.get("status") == "success"
                    ]
                    if durations:
                        avg_duration = sum(durations) / len(durations)
                        if avg_duration > thresholds[f"{operation}_response_threshold"]:
                            alerts.append(
                                {
                                    "type": "response_time",
                                    "severity": "warning",
                                    "message": f"{operation} average response time {avg_duration:.3f}s exceeds threshold {thresholds[f'{operation}_response_threshold']}s",
                                    "value": avg_duration,
                                }
                            )

        return alerts

    def clear_history(self, metric: Optional[str] = None):
        """
        清除历史记录

        Args:
            metric: 可选的指标名称，如未提供则清除所有历史
        """
        if metric:
            if metric in self._performance_history:
                del self._performance_history[metric]
        else:
            self._performance_history.clear()

    def export_performance_report(self) -> Dict[str, Any]:
        """
        导出性能报告

        Returns:
            包含完整性能报告的字典
        """
        return {
            "summary": self.get_performance_summary(),
            "history": self._performance_history,
            "generated_at": datetime.now().isoformat(),
        }


# 全局性能监控实例
_monitor_instance: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """
    获取全局性能监控器实例

    Returns:
        PerformanceMonitor 实例
    """
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PerformanceMonitor()
    return _monitor_instance
