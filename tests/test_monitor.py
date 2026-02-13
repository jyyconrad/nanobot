"""
测试监控和日志记录功能
=======================

测试结构化日志、性能监控、健康检查和告警机制。
"""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nanobot.monitor.structured_logger import get_structured_logger, StructuredLogger
from nanobot.monitor.performance_monitor import get_performance_monitor, PerformanceMonitor
from nanobot.monitor.health_checker import get_health_checker, HealthChecker, HealthCheck
from nanobot.monitor.alert_manager import get_alert_manager, AlertManager, AlertRule, Alert
from nanobot.monitor.diagnostics import get_system_diagnostic, SystemDiagnostic


class TestStructuredLogger:
    """测试结构化日志器"""

    def test_get_structured_logger(self):
        """测试获取全局结构化日志器实例"""
        logger = get_structured_logger()
        assert isinstance(logger, StructuredLogger)

    def test_logging_methods(self):
        """测试日志记录方法"""
        logger = get_structured_logger()

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

    def test_log_performance(self):
        """测试性能日志记录"""
        logger = get_structured_logger()
        logger.log_performance("test_operation", 1.23)
        logger.log_performance("test_operation_failed", 0.5, status="failed")

    def test_log_health_check(self):
        """测试健康检查日志记录"""
        logger = get_structured_logger()
        logger.log_health_check("test_component", "healthy")
        logger.log_health_check("test_component_warning", "warning", "Warning message")
        logger.log_health_check("test_component_error", "unhealthy", "Error message")

    def test_log_alert(self):
        """测试告警日志记录"""
        logger = get_structured_logger()
        logger.log_alert("test_alert", "info", "Info alert")
        logger.log_alert("test_alert", "warning", "Warning alert")
        logger.log_alert("test_alert", "critical", "Critical alert")


class TestPerformanceMonitor:
    """测试性能监控器"""

    def test_get_performance_monitor(self):
        """测试获取全局性能监控器实例"""
        monitor = get_performance_monitor()
        assert isinstance(monitor, PerformanceMonitor)

    def test_get_system_info(self):
        """测试获取系统信息"""
        monitor = get_performance_monitor()
        info = monitor.get_system_info()
        assert isinstance(info, dict)
        assert "memory_usage" in info
        assert "cpu_usage" in info
        assert "uptime" in info

    def test_timer_decorator(self):
        """测试计时器装饰器"""
        monitor = get_performance_monitor()

        @monitor.measure_time("test_operation")
        def test_function():
            import time

            time.sleep(0.01)
            return 42

        result = test_function()
        assert result == 42

    def test_timer_context_manager(self):
        """测试计时器上下文管理器"""
        monitor = get_performance_monitor()

        with monitor.timer("test_context_operation"):
            import time

            time.sleep(0.01)

    def test_record_response_time(self):
        """测试记录响应时间"""
        monitor = get_performance_monitor()
        monitor.record_response_time("/test/endpoint", 0.123)
        monitor.record_response_time("/test/endpoint", 0.5, status_code=404)


class TestHealthChecker:
    """测试健康检查器"""

    def test_get_health_checker(self):
        """测试获取全局健康检查器实例"""
        checker = get_health_checker()
        assert isinstance(checker, HealthChecker)

    def test_run_all_checks(self):
        """测试运行所有健康检查"""
        checker = get_health_checker()
        results = checker.run_all_checks()
        assert isinstance(results, list)
        assert all(isinstance(result, HealthCheck) for result in results)

    def test_get_health_summary(self):
        """测试获取健康检查摘要"""
        checker = get_health_checker()
        summary = checker.get_health_summary()
        assert isinstance(summary, dict)
        assert "status" in summary
        assert "components" in summary
        assert "checks" in summary

    def test_is_healthy(self):
        """测试检查系统是否健康"""
        checker = get_health_checker()
        is_healthy = checker.is_healthy()
        assert isinstance(is_healthy, bool)

    def test_get_failed_checks(self):
        """测试获取失败的健康检查"""
        checker = get_health_checker()
        failed_checks = checker.get_failed_checks()
        assert isinstance(failed_checks, list)


class TestAlertManager:
    """测试告警管理器"""

    def test_get_alert_manager(self):
        """测试获取全局告警管理器实例"""
        manager = get_alert_manager()
        assert isinstance(manager, AlertManager)

    def test_alert_rule_creation(self):
        """测试创建告警规则"""
        manager = get_alert_manager()
        rule = AlertRule(
            rule_id="test_rule",
            alert_type="test",
            severity="warning",
            condition=lambda: False,
            message="Test alert",
        )
        manager.add_rule(rule)
        assert len(manager.get_all_rules()) > 0
        manager.remove_rule("test_rule")

    def test_get_alerts(self):
        """测试获取告警"""
        manager = get_alert_manager()
        alerts = manager.get_alerts()
        assert isinstance(alerts, list)

    def test_get_alert_summary(self):
        """测试获取告警摘要"""
        manager = get_alert_manager()
        summary = manager.get_alert_summary()
        assert isinstance(summary, dict)
        assert "total" in summary
        assert "critical" in summary
        assert "warning" in summary
        assert "info" in summary


class TestSystemDiagnostic:
    """测试系统诊断工具"""

    def test_get_system_diagnostic(self):
        """测试获取全局系统诊断实例"""
        diag = get_system_diagnostic()
        assert isinstance(diag, SystemDiagnostic)

    def test_get_system_info(self):
        """测试获取系统信息"""
        diag = get_system_diagnostic()
        info = diag.get_system_info()
        assert isinstance(info, dict)
        assert "platform" in info
        assert "python_version" in info
        assert "hostname" in info

    def test_get_process_info(self):
        """测试获取进程信息"""
        diag = get_system_diagnostic()
        info = diag.get_process_info()
        assert isinstance(info, dict)
        assert "pid" in info
        assert "name" in info
        assert "cpu_usage" in info
        assert "memory_usage" in info

    def test_run_all_diagnostics(self):
        """测试运行完整诊断"""
        diag = get_system_diagnostic()
        report = diag.run_all_diagnostics()
        assert isinstance(report, dict)
        assert "timestamp" in report
        assert "system_info" in report
        assert "process_info" in report
        assert "resource_usage" in report
        assert "health_check" in report

    def test_export_report(self):
        """测试导出诊断报告"""
        diag = get_system_diagnostic()
        report = diag.export_report()
        assert isinstance(report, str)
        assert len(report) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
