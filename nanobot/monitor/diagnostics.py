"""
诊断工具系统
============

提供系统诊断和调试功能，帮助快速定位和解决问题。

功能特点：
- 系统信息收集
- 进程和线程信息
- 资源使用分析
- 网络连接诊断
- 文件系统检查
"""

import os
import platform
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psutil
from loguru import logger

from nanobot.monitor.health_checker import get_health_checker
from nanobot.monitor.performance_monitor import get_performance_monitor
from nanobot.monitor.structured_logger import get_structured_logger


class SystemDiagnostic:
    """
    系统诊断工具

    提供全面的系统诊断功能。
    """

    def __init__(self):
        self.logger = get_structured_logger()
        self.performance_monitor = get_performance_monitor()
        self.health_checker = get_health_checker()

    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息

        Returns:
            系统信息字典
        """
        info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
            "python_version_info": {
                "major": sys.version_info.major,
                "minor": sys.version_info.minor,
                "micro": sys.version_info.micro,
                "releaselevel": sys.version_info.releaselevel,
                "serial": sys.version_info.serial,
            },
            "hostname": platform.node(),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        }

        # 操作系统特定信息
        if platform.system() == "Darwin":
            info["mac_version"] = platform.mac_ver()
        elif platform.system() == "Linux":
            try:
                import distro

                info["linux_distribution"] = distro.linux_distribution()
            except ImportError:
                logger.debug("distro module not available for Linux distribution info")

        return info

    def get_process_info(self) -> Dict[str, Any]:
        """
        获取当前进程信息

        Returns:
            进程信息字典
        """
        process = psutil.Process(os.getpid())

        info = {
            "pid": process.pid,
            "name": process.name(),
            "status": process.status(),
            "username": process.username(),
            "cpu_usage": process.cpu_percent(interval=0.1),
            "memory_usage": process.memory_info().rss / (1024 * 1024),  # MB
            "memory_percent": process.memory_percent(),
            "threads": process.num_threads(),
            "created": datetime.fromtimestamp(process.create_time()).isoformat(),
            "uptime": (
                datetime.now() - datetime.fromtimestamp(process.create_time())
            ).total_seconds(),
        }

        return info

    def get_thread_info(self) -> List[Dict[str, Any]]:
        """
        获取线程信息

        Returns:
            线程信息列表
        """
        process = psutil.Process(os.getpid())
        threads = []

        for thread in process.threads():
            threads.append(
                {
                    "id": thread.id,
                    "user_time": thread.user_time,
                    "system_time": thread.system_time,
                }
            )

        return threads

    def get_resource_usage(self) -> Dict[str, Any]:
        """
        获取系统资源使用情况

        Returns:
            资源使用情况字典
        """
        system_info = self.performance_monitor.get_system_info()
        process_info = self.get_process_info()

        disk_usage = psutil.disk_usage("/")
        disk_io = psutil.disk_io_counters()
        network_io = psutil.net_io_counters()

        return {
            "system_memory": {
                "total": system_info.get("system_memory_total", 0),
                "available": system_info.get("system_memory_available", 0),
                "used": system_info.get("system_memory_used", 0),
                "percent": system_info.get("system_memory_percent", 0),
            },
            "system_cpu": {
                "percent": system_info.get("cpu_usage", 0),
            },
            "disk": {
                "total": disk_usage.total / (1024 * 1024 * 1024),
                "used": disk_usage.used / (1024 * 1024 * 1024),
                "free": disk_usage.free / (1024 * 1024 * 1024),
                "percent": disk_usage.percent,
            },
            "disk_io": {
                "read_count": disk_io.read_count,
                "write_count": disk_io.write_count,
                "read_bytes": disk_io.read_bytes,
                "write_bytes": disk_io.write_bytes,
            },
            "network_io": {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv,
            },
            "process": {
                "cpu_percent": process_info["cpu_usage"],
                "memory_mb": process_info["memory_usage"],
                "memory_percent": process_info["memory_percent"],
                "threads": process_info["threads"],
            },
        }

    def get_network_info(self) -> Dict[str, Any]:
        """
        获取网络信息

        Returns:
            网络信息字典
        """
        interfaces = {}
        for name, addrs in psutil.net_if_addrs().items():
            interface = {
                "addresses": [],
                "stats": psutil.net_if_stats()[name],
            }
            for addr in addrs:
                interface["addresses"].append(
                    {
                        "family": addr.family.name,
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast,
                    }
                )
            interfaces[name] = interface

        return {
            "interfaces": interfaces,
            "connections": self.get_network_connections(),
        }

    def get_network_connections(self) -> List[Dict[str, Any]]:
        """
        获取网络连接

        Returns:
            网络连接列表
        """
        connections = []
        try:
            for conn in psutil.net_connections(kind="inet"):
                connections.append(
                    {
                        "fd": conn.fd,
                        "family": conn.family.name,
                        "type": conn.type.name,
                        "laddr": conn.laddr,
                        "raddr": conn.raddr,
                        "status": conn.status,
                        "pid": conn.pid,
                    }
                )
        except Exception as e:
            logger.debug(f"Failed to get network connections: {e}")

        return connections

    def get_file_handles(self) -> List[Dict[str, Any]]:
        """
        获取打开的文件句柄

        Returns:
            文件句柄列表
        """
        process = psutil.Process(os.getpid())
        files = []

        try:
            for file in process.open_files():
                files.append(
                    {
                        "path": file.path,
                        "fd": file.fd,
                        "position": file.position,
                        "mode": file.mode,
                    }
                )
        except Exception as e:
            logger.debug(f"Failed to get file handles: {e}")

        return files

    def get_environment_variables(self) -> Dict[str, str]:
        """
        获取环境变量

        Returns:
            环境变量字典（筛选后的）
        """
        env = os.environ.copy()
        # 过滤掉敏感信息
        sensitive_keys = [
            "API_KEY",
            "SECRET",
            "PASSWORD",
            "TOKEN",
            "ACCESS_KEY",
            "API_SECRET",
        ]

        filtered_env = {}
        for key, value in env.items():
            if any(sensitive in key.upper() for sensitive in sensitive_keys):
                filtered_env[key] = "[REDACTED]"
            else:
                filtered_env[key] = value

        return filtered_env

    def run_all_diagnostics(self) -> Dict[str, Any]:
        """
        运行所有诊断

        Returns:
            完整的诊断报告
        """
        logger.info("Running full system diagnostics...")

        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "system_info": self.get_system_info(),
                "process_info": self.get_process_info(),
                "thread_info": self.get_thread_info(),
                "resource_usage": self.get_resource_usage(),
                "network_info": self.get_network_info(),
                "file_handles": self.get_file_handles(),
                "environment_variables": self.get_environment_variables(),
                "health_check": self.health_checker.get_health_summary(),
                "performance_summary": self.performance_monitor.get_performance_summary(),
            }

            logger.info("Diagnostics completed successfully")
            return report
        except Exception as e:
            logger.error(f"Diagnostics failed: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def export_report(self) -> str:
        """
        导出诊断报告（JSON 字符串）

        Returns:
            诊断报告的 JSON 字符串
        """
        import json

        report = self.run_all_diagnostics()
        return json.dumps(report, ensure_ascii=False, indent=2)

    def save_report(self, filename: str):
        """
        保存诊断报告到文件

        Args:
            filename: 文件路径
        """
        report = self.export_report()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"Diagnostic report saved to {filename}")

    def get_resource_leaks(self) -> List[Dict[str, Any]]:
        """
        查找可能的资源泄漏

        Returns:
            资源泄漏列表
        """
        leaks = []

        # 检查文件句柄数量
        file_count = len(self.get_file_handles())
        if file_count > 100:
            leaks.append(
                {
                    "type": "file_handles",
                    "message": f"Too many open file handles: {file_count}",
                    "count": file_count,
                }
            )

        return leaks

    def get_thread_deadlocks(self) -> List[Dict[str, Any]]:
        """
        检查线程死锁

        Returns:
            可能的死锁列表
        """
        # 简单的死锁检测（基于线程数量和状态）
        deadlocks = []
        threads = self.get_thread_info()

        # 注意：这是一个简单的死锁检测方法
        # 在生产环境中，可能需要使用更复杂的方法
        if len(threads) > 50:
            deadlocks.append(
                {
                    "type": "thread_count",
                    "message": f"High thread count: {len(threads)}",
                    "count": len(threads),
                }
            )

        return deadlocks


# 全局诊断工具实例
_diagnostic_instance: Optional[SystemDiagnostic] = None


def get_system_diagnostic() -> SystemDiagnostic:
    """
    获取全局系统诊断实例

    Returns:
        SystemDiagnostic 实例
    """
    global _diagnostic_instance
    if _diagnostic_instance is None:
        _diagnostic_instance = SystemDiagnostic()
    return _diagnostic_instance


# 便捷方法
def run_diagnostic() -> Dict[str, Any]:
    """
    运行系统诊断（便捷方法）

    Returns:
        诊断报告
    """
    return get_system_diagnostic().run_all_diagnostics()


def export_diagnostic_report(filename: str):
    """
    导出诊断报告到文件（便捷方法）

    Args:
        filename: 文件路径
    """
    get_system_diagnostic().save_report(filename)


def check_for_resource_leaks() -> List[Dict[str, Any]]:
    """
    检查资源泄漏（便捷方法）

    Returns:
        资源泄漏列表
    """
    return get_system_diagnostic().get_resource_leaks()
