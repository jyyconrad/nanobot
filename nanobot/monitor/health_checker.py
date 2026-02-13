"""
健康检查系统
============

提供系统健康检查功能，确保各个组件正常运行。

功能特点：
- 组件健康状态检查
- 系统资源检查
- 服务可用性检查
- 数据库连接检查
- 外部API可用性检查
"""

import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from nanobot.monitor.performance_monitor import get_performance_monitor
from nanobot.monitor.structured_logger import get_structured_logger


class HealthCheck:
    """
    健康检查结果

    表示单个组件的健康检查结果
    """

    def __init__(
        self,
        component: str,
        status: str,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化健康检查结果

        Args:
            component: 组件名称
            status: 健康状态（healthy/unhealthy/warning）
            message: 检查消息
            details: 详细信息
        """
        self.component = component
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典表示

        Returns:
            字典表示的健康检查结果
        """
        return {
            "component": self.component,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
        }


class HealthChecker:
    """
    健康检查器

    用于执行系统各组件的健康检查。
    """

    def __init__(self):
        self.logger = get_structured_logger()
        self.performance_monitor = get_performance_monitor()
        self._checks: List[Callable[[], HealthCheck]] = []

    def register_check(self, check: Callable[[], HealthCheck]):
        """
        注册一个健康检查

        Args:
            check: 健康检查函数
        """
        self._checks.append(check)

    def unregister_check(self, check: Callable[[], HealthCheck]):
        """
        注销一个健康检查

        Args:
            check: 健康检查函数
        """
        if check in self._checks:
            self._checks.remove(check)

    def run_all_checks(self) -> List[HealthCheck]:
        """
        运行所有健康检查

        Returns:
            所有健康检查结果的列表
        """
        results = []
        for check in self._checks:
            try:
                result = check()
                results.append(result)

                # 记录检查结果
                self.logger.log_health_check(
                    result.component,
                    result.status,
                    result.message,
                    **result.details,
                )
            except Exception as e:
                logger.error(f"Health check {check.__name__} failed: {e}")
                results.append(
                    HealthCheck(
                        component=check.__name__,
                        status="unhealthy",
                        message=f"Health check failed: {e}",
                    )
                )
        return results

    def get_health_summary(self) -> Dict[str, Any]:
        """
        获取健康检查摘要

        Returns:
            包含系统健康状态的字典
        """
        results = self.run_all_checks()
        healthy_count = sum(1 for r in results if r.status == "healthy")
        warning_count = sum(1 for r in results if r.status == "warning")
        unhealthy_count = sum(1 for r in results if r.status == "unhealthy")

        # 确定整体健康状态
        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif warning_count > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"

        summary = {
            "timestamp": datetime.now().isoformat(),
            "status": overall_status,
            "components": {
                "healthy": healthy_count,
                "warning": warning_count,
                "unhealthy": unhealthy_count,
                "total": len(results),
            },
            "checks": [result.to_dict() for result in results],
        }

        return summary

    def is_healthy(self) -> bool:
        """
        检查系统是否健康

        Returns:
            如果系统健康返回 True，否则返回 False
        """
        results = self.run_all_checks()
        return all(result.status == "healthy" for result in results)

    def get_failed_checks(self) -> List[HealthCheck]:
        """
        获取失败的健康检查

        Returns:
            失败的健康检查列表
        """
        results = self.run_all_checks()
        return [result for result in results if result.status != "healthy"]


# 系统级健康检查
def _check_system_resources() -> HealthCheck:
    """
    检查系统资源使用情况
    """
    monitor = get_performance_monitor()
    system_info = monitor.get_system_info()

    # 检查内存使用（警告：> 80%，严重：> 90%）
    if system_info["memory_usage"] > 90:
        return HealthCheck(
            component="system.memory",
            status="unhealthy",
            message=f"Memory usage too high: {system_info['memory_usage']:.1f}%",
            details={"usage": system_info["memory_usage"]},
        )
    elif system_info["memory_usage"] > 80:
        return HealthCheck(
            component="system.memory",
            status="warning",
            message=f"Memory usage high: {system_info['memory_usage']:.1f}%",
            details={"usage": system_info["memory_usage"]},
        )

    # 检查 CPU 使用（警告：> 80%，严重：> 95%）
    if system_info["cpu_usage"] > 95:
        return HealthCheck(
            component="system.cpu",
            status="unhealthy",
            message=f"CPU usage too high: {system_info['cpu_usage']:.1f}%",
            details={"usage": system_info["cpu_usage"]},
        )
    elif system_info["cpu_usage"] > 80:
        return HealthCheck(
            component="system.cpu",
            status="warning",
            message=f"CPU usage high: {system_info['cpu_usage']:.1f}%",
            details={"usage": system_info["cpu_usage"]},
        )

    # 检查磁盘使用（警告：> 80%，严重：> 90%）
    if "disk_percent" in system_info:
        if system_info["disk_percent"] > 90:
            return HealthCheck(
                component="system.disk",
                status="unhealthy",
                message=f"Disk usage too high: {system_info['disk_percent']:.1f}%",
                details={"usage": system_info["disk_percent"]},
            )
        elif system_info["disk_percent"] > 80:
            return HealthCheck(
                component="system.disk",
                status="warning",
                message=f"Disk usage high: {system_info['disk_percent']:.1f}%",
                details={"usage": system_info["disk_percent"]},
            )

    return HealthCheck(
        component="system.resources",
        status="healthy",
        message="System resources within healthy limits",
        details=system_info,
    )


def _check_application_uptime() -> HealthCheck:
    """
    检查应用程序运行时间
    """
    monitor = get_performance_monitor()
    system_info = monitor.get_system_info()
    uptime = system_info["uptime"]

    if uptime < 60:
        return HealthCheck(
            component="application.uptime",
            status="warning",
            message=f"Application just started ({uptime:.0f} seconds)",
            details={"uptime": uptime},
        )

    return HealthCheck(
        component="application.uptime",
        status="healthy",
        message=f"Application running for {uptime:.0f} seconds",
        details={"uptime": uptime},
    )


def _check_network_connectivity() -> HealthCheck:
    """
    检查网络连接性
    """
    try:
        import socket
        import urllib.request

        # 尝试连接到公共 DNS 服务器
        socket.create_connection(("8.8.8.8", 53), timeout=5)

        # 尝试访问一个简单的 HTTP 服务
        urllib.request.urlopen("http://www.baidu.com", timeout=5)

        return HealthCheck(
            component="network.connectivity",
            status="healthy",
            message="Network connectivity is good",
        )
    except Exception as e:
        logger.error(f"Network connectivity check failed: {e}")
        return HealthCheck(
            component="network.connectivity",
            status="unhealthy",
            message=f"Network connectivity issue: {e}",
        )


def _check_database_connection() -> HealthCheck:
    """
    检查数据库连接（如果有）
    """
    try:
        from nanobot.storage.database import get_database

        db = get_database()
        # 简单的查询来检查连接
        if db.is_connected():
            return HealthCheck(
                component="database.connection",
                status="healthy",
                message="Database connection is working",
            )
        else:
            return HealthCheck(
                component="database.connection",
                status="unhealthy",
                message="Database connection is not available",
            )
    except ImportError:
        logger.debug("Database module not available, skipping check")
        return HealthCheck(
            component="database.connection",
            status="healthy",
            message="Database module not available",
        )
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return HealthCheck(
            component="database.connection",
            status="unhealthy",
            message=f"Database connection error: {e}",
        )


# 全局健康检查器实例
_health_checker_instance: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """
    获取全局健康检查器实例

    Returns:
        HealthChecker 实例
    """
    global _health_checker_instance
    if _health_checker_instance is None:
        _health_checker_instance = HealthChecker()

        # 注册系统级健康检查
        _health_checker_instance.register_check(_check_system_resources)
        _health_checker_instance.register_check(_check_application_uptime)
        _health_checker_instance.register_check(_check_network_connectivity)
        _health_checker_instance.register_check(_check_database_connection)

    return _health_checker_instance
