"""
告警管理系统
============

提供告警机制，用于监控系统状态并在需要时发送告警。

功能特点：
- 告警规则配置
- 告警发送
- 告警降级
- 告警历史记录
- 告警通知渠道
"""

import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from nanobot.monitor.health_checker import HealthCheck, get_health_checker
from nanobot.monitor.performance_monitor import get_performance_monitor
from nanobot.monitor.structured_logger import get_structured_logger


class Alert:
    """
    告警对象

    表示一个具体的告警实例
    """

    def __init__(
        self,
        alert_id: str,
        alert_type: str,
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ):
        """
        初始化告警

        Args:
            alert_id: 告警 ID
            alert_type: 告警类型
            severity: 严重程度（critical/warning/info）
            message: 告警消息
            details: 详细信息
            timestamp: 告警时间戳
        """
        self.alert_id = alert_id
        self.alert_type = alert_type
        self.severity = severity
        self.message = message
        self.details = details or {}
        self.timestamp = timestamp or datetime.now().isoformat()
        self.acknowledged = False
        self.acknowledged_at: Optional[str] = None
        self.acknowledged_by: Optional[str] = None
        self.resolved = False
        self.resolved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典表示

        Returns:
            字典表示的告警
        """
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at,
            "acknowledged_by": self.acknowledged_by,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at,
        }

    def acknowledge(self, user: str):
        """
        确认告警

        Args:
            user: 确认人
        """
        self.acknowledged = True
        self.acknowledged_at = datetime.now().isoformat()
        self.acknowledged_by = user

    def resolve(self):
        """
        解决告警
        """
        self.resolved = True
        self.resolved_at = datetime.now().isoformat()


class AlertRule:
    """
    告警规则

    定义何时触发告警的条件
    """

    def __init__(
        self,
        rule_id: str,
        alert_type: str,
        severity: str,
        condition: Callable[[], bool],
        message: str,
        details: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        repeat_interval: int = 3600,
    ):
        """
        初始化告警规则

        Args:
            rule_id: 规则 ID
            alert_type: 告警类型
            severity: 严重程度（critical/warning/info）
            condition: 触发条件（返回 True 表示触发）
            message: 告警消息
            details: 详细信息
            enabled: 是否启用规则
            repeat_interval: 重复告警间隔（秒）
        """
        self.rule_id = rule_id
        self.alert_type = alert_type
        self.severity = severity
        self.condition = condition
        self.message = message
        self.details = details or {}
        self.enabled = enabled
        self.repeat_interval = repeat_interval
        self._last_triggered: Optional[str] = None

    def should_trigger(self) -> bool:
        """
        检查是否应该触发告警

        Returns:
            如果应该触发返回 True，否则返回 False
        """
        if not self.enabled:
            return False

        # 检查条件是否满足
        if not self.condition():
            return False

        # 检查是否在重复间隔内
        if self._last_triggered:
            last_time = datetime.fromisoformat(self._last_triggered)
            now = datetime.now()
            if (now - last_time).total_seconds() < self.repeat_interval:
                return False

        return True

    def trigger(self) -> Alert:
        """
        触发告警

        Returns:
            新的告警实例
        """
        self._last_triggered = datetime.now().isoformat()
        alert = Alert(
            alert_id=f"{self.rule_id}-{int(time.time())}",
            alert_type=self.alert_type,
            severity=self.severity,
            message=self.message,
            details=self.details,
        )
        return alert


class AlertManager:
    """
    告警管理器

    负责管理告警规则和发送告警
    """

    def __init__(self):
        self.logger = get_structured_logger()
        self.health_checker = get_health_checker()
        self.performance_monitor = get_performance_monitor()
        self._rules: Dict[str, AlertRule] = {}
        self._alerts: Dict[str, Alert] = {}
        self._notification_handlers: List[Callable[[Alert], None]] = []

    def add_rule(self, rule: AlertRule):
        """
        添加告警规则

        Args:
            rule: 告警规则
        """
        self._rules[rule.rule_id] = rule

    def remove_rule(self, rule_id: str):
        """
        删除告警规则

        Args:
            rule_id: 规则 ID
        """
        if rule_id in self._rules:
            del self._rules[rule_id]

    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """
        获取告警规则

        Args:
            rule_id: 规则 ID

        Returns:
            告警规则或 None
        """
        return self._rules.get(rule_id)

    def get_all_rules(self) -> List[AlertRule]:
        """
        获取所有告警规则

        Returns:
            告警规则列表
        """
        return list(self._rules.values())

    def add_notification_handler(self, handler: Callable[[Alert], None]):
        """
        添加告警通知处理器

        Args:
            handler: 通知处理器（接受 Alert 对象）
        """
        self._notification_handlers.append(handler)

    def remove_notification_handler(self, handler: Callable[[Alert], None]):
        """
        移除告警通知处理器

        Args:
            handler: 通知处理器
        """
        if handler in self._notification_handlers:
            self._notification_handlers.remove(handler)

    def check_rules(self) -> List[Alert]:
        """
        检查所有告警规则并触发告警

        Returns:
            触发的新告警列表
        """
        new_alerts = []

        for rule in self._rules.values():
            if rule.should_trigger():
                try:
                    alert = rule.trigger()
                    self._alerts[alert.alert_id] = alert
                    new_alerts.append(alert)

                    # 记录告警
                    self.logger.log_alert(
                        alert.alert_type,
                        alert.severity,
                        alert.message,
                        **alert.details,
                    )

                    # 发送通知
                    self._send_notifications(alert)
                except Exception as e:
                    logger.error(
                        f"Failed to trigger alert for rule {rule.rule_id}: {e}"
                    )

        return new_alerts

    def _send_notifications(self, alert: Alert):
        """
        发送告警通知

        Args:
            alert: 告警对象
        """
        for handler in self._notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")

    def get_alerts(
        self,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        resolved: Optional[bool] = None,
    ) -> List[Alert]:
        """
        获取告警

        Args:
            severity: 严重程度过滤（critical/warning/info）
            acknowledged: 是否已确认（True/False）
            resolved: 是否已解决（True/False）

        Returns:
            符合条件的告警列表
        """
        alerts = list(self._alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]

        return alerts

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """
        获取特定告警

        Args:
            alert_id: 告警 ID

        Returns:
            告警对象或 None
        """
        return self._alerts.get(alert_id)

    def acknowledge_alert(self, alert_id: str, user: str):
        """
        确认告警

        Args:
            alert_id: 告警 ID
            user: 确认人
        """
        if alert_id in self._alerts:
            self._alerts[alert_id].acknowledge(user)

    def resolve_alert(self, alert_id: str):
        """
        解决告警

        Args:
            alert_id: 告警 ID
        """
        if alert_id in self._alerts:
            self._alerts[alert_id].resolve()

    def get_alert_summary(self) -> Dict[str, Any]:
        """
        获取告警摘要

        Returns:
            告警摘要字典
        """
        alerts = self.get_alerts()
        summary = {
            "total": len(alerts),
            "critical": len(
                [a for a in alerts if a.severity == "critical" and not a.resolved]
            ),
            "warning": len(
                [a for a in alerts if a.severity == "warning" and not a.resolved]
            ),
            "info": len([a for a in alerts if a.severity == "info" and not a.resolved]),
            "acknowledged": len(
                [a for a in alerts if a.acknowledged and not a.resolved]
            ),
            "resolved": len([a for a in alerts if a.resolved]),
        }
        return summary

    def export_alerts(self) -> List[Dict[str, Any]]:
        """
        导出所有告警（字典格式）

        Returns:
            所有告警的字典列表
        """
        return [alert.to_dict() for alert in self._alerts.values()]

    def clear_alerts(self):
        """
        清除所有告警
        """
        self._alerts.clear()

    def run_health_check_alerts(self) -> List[Alert]:
        """
        运行健康检查告警

        Returns:
            触发的健康检查告警列表
        """
        failed_checks = self.health_checker.get_failed_checks()
        new_alerts = []

        for check in failed_checks:
            alert = Alert(
                alert_id=f"health-check-{check.component}-{int(time.time())}",
                alert_type="health",
                severity="warning" if check.status == "warning" else "critical",
                message=check.message,
                details=check.details,
            )

            self._alerts[alert.alert_id] = alert
            new_alerts.append(alert)

            # 记录告警
            self.logger.log_alert(
                alert.alert_type,
                alert.severity,
                alert.message,
                **alert.details,
            )

            # 发送通知
            self._send_notifications(alert)

        return new_alerts

    def run_performance_alerts(self, thresholds: Dict[str, Any]) -> List[Alert]:
        """
        运行性能告警

        Args:
            thresholds: 性能阈值配置

        Returns:
            触发的性能告警列表
        """
        performance_alerts = self.performance_monitor.check_performance_thresholds(
            thresholds
        )
        new_alerts = []

        for alert_info in performance_alerts:
            alert = Alert(
                alert_id=f"performance-{alert_info['type']}-{int(time.time())}",
                alert_type=alert_info["type"],
                severity=alert_info["severity"],
                message=alert_info["message"],
                details={"value": alert_info["value"]},
            )

            self._alerts[alert.alert_id] = alert
            new_alerts.append(alert)

            # 记录告警
            self.logger.log_alert(
                alert.alert_type,
                alert.severity,
                alert.message,
                **alert.details,
            )

            # 发送通知
            self._send_notifications(alert)

        return new_alerts


# 创建默认的告警规则
def _create_default_alert_rules(manager: AlertManager):
    """
    创建默认的告警规则
    """
    # 系统资源告警规则
    manager.add_rule(
        AlertRule(
            rule_id="sys.memory.critical",
            alert_type="memory",
            severity="critical",
            condition=lambda: get_performance_monitor().get_system_info()[
                "memory_usage"
            ]
            > 90,
            message="Critical memory usage",
            details={"threshold": 90},
            repeat_interval=1800,
        )
    )

    manager.add_rule(
        AlertRule(
            rule_id="sys.memory.warning",
            alert_type="memory",
            severity="warning",
            condition=lambda: get_performance_monitor().get_system_info()[
                "memory_usage"
            ]
            > 80,
            message="High memory usage",
            details={"threshold": 80},
            repeat_interval=3600,
        )
    )

    manager.add_rule(
        AlertRule(
            rule_id="sys.cpu.critical",
            alert_type="cpu",
            severity="critical",
            condition=lambda: get_performance_monitor().get_system_info()["cpu_usage"]
            > 95,
            message="Critical CPU usage",
            details={"threshold": 95},
            repeat_interval=1800,
        )
    )

    manager.add_rule(
        AlertRule(
            rule_id="sys.cpu.warning",
            alert_type="cpu",
            severity="warning",
            condition=lambda: get_performance_monitor().get_system_info()["cpu_usage"]
            > 80,
            message="High CPU usage",
            details={"threshold": 80},
            repeat_interval=3600,
        )
    )

    # 健康检查告警规则
    manager.add_rule(
        AlertRule(
            rule_id="health.check.failed",
            alert_type="health",
            severity="warning",
            condition=lambda: len(get_health_checker().get_failed_checks()) > 0,
            message="Health check failed",
            details={"failed_checks": len(get_health_checker().get_failed_checks())},
            repeat_interval=600,
        )
    )

    # 网络连接告警规则
    manager.add_rule(
        AlertRule(
            rule_id="network.connectivity.failed",
            alert_type="network",
            severity="warning",
            condition=lambda: get_health_checker().get_failed_checks()
            and any(
                check.component == "network.connectivity"
                for check in get_health_checker().get_failed_checks()
            ),
            message="Network connectivity issue",
            repeat_interval=300,
        )
    )


# 全局告警管理器实例
_alert_manager_instance: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """
    获取全局告警管理器实例

    Returns:
        AlertManager 实例
    """
    global _alert_manager_instance
    if _alert_manager_instance is None:
        _alert_manager_instance = AlertManager()
        _create_default_alert_rules(_alert_manager_instance)
    return _alert_manager_instance
