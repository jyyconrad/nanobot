"""
健康检查和自动恢复模块
"""

import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from loguru import logger

from .state_tracker import AgentState, StateTracker


@dataclass
class HealthCheckResult:
    """健康检查结果"""

    check_name: str
    is_healthy: bool
    message: str
    timestamp: float = field(default_factory=time.time)
    duration: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


class HealthChecker:
    """健康检查器"""

    def __init__(self, state_tracker: Optional[StateTracker] = None):
        self.state_tracker = state_tracker
        self._checks = []
        self._recovery_actions = []
        self._last_check: Optional[HealthCheckResult] = None
        self._is_running = False
        self._check_thread: Optional[threading.Thread] = None
        self._interval = 30  # 检查间隔（秒）

    def register_check(
        self, check_name: str, check_func, recovery_action=None, description: str = ""
    ):
        """
        注册健康检查

        Args:
            check_name: 检查名称
            check_func: 检查函数，返回 (is_healthy, message, details)
            recovery_action: 恢复操作函数，可选
            description: 检查描述
        """
        self._checks.append(
            {
                "name": check_name,
                "func": check_func,
                "recovery": recovery_action,
                "description": description,
            }
        )

    def register_recovery_action(self, name: str, action, description: str = ""):
        """
        注册恢复操作

        Args:
            name: 操作名称
            action: 操作函数
            description: 操作描述
        """
        self._recovery_actions.append(
            {"name": name, "action": action, "description": description}
        )

    def run_all_checks(self) -> List[HealthCheckResult]:
        """运行所有健康检查"""
        results = []
        for check in self._checks:
            start_time = time.time()
            try:
                is_healthy, message, details = check["func"]()
                duration = time.time() - start_time
                results.append(
                    HealthCheckResult(
                        check_name=check["name"],
                        is_healthy=is_healthy,
                        message=message,
                        duration=duration,
                        details=details or {},
                    )
                )
            except Exception as e:
                duration = time.time() - start_time
                results.append(
                    HealthCheckResult(
                        check_name=check["name"],
                        is_healthy=False,
                        message=f"Check failed: {str(e)}",
                        duration=duration,
                        details={"error": str(e)},
                    )
                )
                logger.error(f"Health check failed: {check['name']} - {e}")

        self._last_check = results[0] if results else None
        return results

    def get_health_status(self) -> Dict[str, Any]:
        """获取整体健康状态"""
        checks = self.run_all_checks()
        all_healthy = all(check.is_healthy for check in checks)
        unhealthy_checks = [check for check in checks if not check.is_healthy]

        status = {
            "healthy": all_healthy,
            "timestamp": time.time(),
            "check_count": len(checks),
            "healthy_count": len([c for c in checks if c.is_healthy]),
            "unhealthy_count": len(unhealthy_checks),
            "checks": [
                {
                    "name": check.check_name,
                    "healthy": check.is_healthy,
                    "message": check.message,
                    "duration": check.duration,
                    "details": check.details,
                }
                for check in checks
            ],
        }

        if self.state_tracker:
            status["agent_state"] = {
                "state": self.state_tracker.get_state().value,
                "uptime": self.state_tracker.get_uptime(),
                "last_heartbeat": time.time() - self.state_tracker.get_last_heartbeat(),
            }

        return status

    def perform_recovery(self, check_name: str) -> bool:
        """
        对特定检查执行恢复操作

        Args:
            check_name: 检查名称

        Returns:
            是否成功执行恢复
        """
        for check in self._checks:
            if check["name"] == check_name and check["recovery"]:
                try:
                    logger.info(f"Performing recovery for {check_name}")
                    check["recovery"]()
                    logger.info(f"Recovery successful for {check_name}")
                    return True
                except Exception as e:
                    logger.error(f"Recovery failed for {check_name}: {e}")
                    return False

        logger.warning(f"No recovery action found for {check_name}")
        return False

    def auto_recover(self) -> List[Dict[str, Any]]:
        """自动执行恢复操作"""
        results = []
        checks = self.run_all_checks()

        for check in checks:
            if not check.is_healthy:
                recovered = self.perform_recovery(check.check_name)
                results.append(
                    {
                        "check_name": check.check_name,
                        "recovered": recovered,
                        "original_message": check.message,
                        "timestamp": time.time(),
                    }
                )

                if recovered:
                    logger.info(f"Auto-recovered from {check.check_name}")
                else:
                    logger.error(f"Auto-recovery failed for {check.check_name}")

        return results

    def start_continuous_monitoring(self, interval: int = 30):
        """
        启动持续监控

        Args:
            interval: 检查间隔（秒）
        """
        self._interval = interval
        self._is_running = True

        def monitor_loop():
            while self._is_running:
                try:
                    status = self.get_health_status()
                    if not status["healthy"]:
                        logger.warning(f"Health check failed: {status}")
                        self.auto_recover()
                except Exception as e:
                    logger.error(f"Health monitoring failed: {e}")

                time.sleep(self._interval)

        self._check_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._check_thread.start()
        logger.info(f"Continuous health monitoring started with interval: {interval}s")

    def stop_continuous_monitoring(self):
        """停止持续监控"""
        self._is_running = False
        if self._check_thread:
            self._check_thread.join(timeout=10)
            self._check_thread = None
        logger.info("Continuous health monitoring stopped")

    def is_running(self) -> bool:
        """检查是否正在运行持续监控"""
        return self._is_running


def create_default_health_checker(state_tracker: StateTracker) -> HealthChecker:
    """创建默认的健康检查器"""
    checker = HealthChecker(state_tracker)

    # 检查Agent状态
    def check_agent_alive():
        is_alive = state_tracker.is_alive()
        if is_alive:
            return (
                True,
                "Agent is alive and responding",
                {
                    "last_heartbeat": time.time() - state_tracker.get_last_heartbeat(),
                    "uptime": state_tracker.get_uptime(),
                },
            )
        else:
            return (
                False,
                "Agent is not responding",
                {"last_heartbeat": time.time() - state_tracker.get_last_heartbeat()},
            )

    checker.register_check("agent_alive", check_agent_alive)

    # 检查CPU使用率
    def check_cpu_usage():
        try:
            import psutil

            cpu_usage = psutil.cpu_percent(interval=1)
            if cpu_usage > 90:
                return (
                    False,
                    f"High CPU usage: {cpu_usage:.1f}%",
                    {"usage": cpu_usage},
                )
            return (True, f"CPU usage: {cpu_usage:.1f}%", {"usage": cpu_usage})
        except Exception as e:
            return (False, f"CPU check failed: {e}", {"error": str(e)})

    checker.register_check("cpu_usage", check_cpu_usage)

    # 检查内存使用率
    def check_memory_usage():
        try:
            import psutil

            memory_usage = psutil.virtual_memory().percent
            if memory_usage > 90:
                return (
                    False,
                    f"High memory usage: {memory_usage:.1f}%",
                    {"usage": memory_usage},
                )
            return (True, f"Memory usage: {memory_usage:.1f}%", {"usage": memory_usage})
        except Exception as e:
            return (False, f"Memory check failed: {e}", {"error": str(e)})

    checker.register_check("memory_usage", check_memory_usage)

    return checker
