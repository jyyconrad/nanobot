"""
结构化日志系统
==============

提供结构化日志记录功能，支持 JSON 格式输出，便于日志收集和分析。

功能特点：
- 支持多种日志格式（JSON、文本）
- 自动添加上下文信息（时间戳、级别、模块、线程）
- 支持日志轮转和压缩
- 提供性能监控日志
- 集成健康检查和告警日志
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from loguru import logger


class StructuredLogger:
    """
    结构化日志记录器

    提供统一的日志接口，支持结构化输出和性能监控。
    """

    def __init__(
        self,
        name: str = "nanobot",
        log_dir: str = "~/.nanobot/logs",
        level: str = "INFO",
        format: str = "json",
    ):
        """
        初始化结构化日志器

        Args:
            name: 日志器名称
            log_dir: 日志存储目录
            level: 日志级别
            format: 输出格式（json 或 text）
        """
        self.name = name
        self.log_dir = Path(log_dir).expanduser()
        self.level = level.upper()
        self.format = format.lower()

        # 确保日志目录存在
        self.log_dir.mkdir(exist_ok=True, parents=True)

        # 配置 loguru
        self._configure_loguru()

    def _configure_loguru(self):
        """配置 loguru 日志器"""
        # 移除默认配置
        logger.remove()

        # 控制台输出
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

        logger.add(
            sys.stdout,
            format=console_format,
            level=self.level,
            colorize=True,
        )

        # 文件输出 - 结构化格式
        log_file = self.log_dir / "nanobot.log"

        if self.format == "json":
            logger.add(
                log_file,
                format=self._json_formatter,
                level=self.level,
                rotation="100 MB",
                retention="30 days",
                compression="gz",
            )
        else:
            logger.add(
                log_file,
                format=console_format,
                level=self.level,
                rotation="100 MB",
                retention="30 days",
                compression="gz",
            )

    def _json_formatter(self, record: Dict[str, Any]) -> str:
        """
        JSON 格式化器

        Args:
            record: loguru 记录字典

        Returns:
            JSON 格式字符串
        """
        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "module": record["name"],
            "function": record["function"],
            "line": record["line"],
            "message": record["message"],
            "thread_id": record["thread"].id,
            "process_id": record["process"].id,
        }

        # 添加额外上下文信息
        if record.get("extra"):
            log_entry["context"] = record["extra"]

        return json.dumps(log_entry) + "\n"

    def debug(self, message: str, **kwargs):
        """
        输出 DEBUG 级别的日志

        Args:
            message: 日志消息
            **kwargs: 额外的上下文信息
        """
        if kwargs:
            logger.debug(message, context=kwargs)
        else:
            logger.debug(message)

    def info(self, message: str, **kwargs):
        """
        输出 INFO 级别的日志

        Args:
            message: 日志消息
            **kwargs: 额外的上下文信息
        """
        if kwargs:
            logger.info(message, context=kwargs)
        else:
            logger.info(message)

    def warning(self, message: str, **kwargs):
        """
        输出 WARNING 级别的日志

        Args:
            message: 日志消息
            **kwargs: 额外的上下文信息
        """
        if kwargs:
            logger.warning(message, context=kwargs)
        else:
            logger.warning(message)

    def error(self, message: str, **kwargs):
        """
        输出 ERROR 级别的日志

        Args:
            message: 日志消息
            **kwargs: 额外的上下文信息
        """
        if kwargs:
            logger.error(message, context=kwargs)
        else:
            logger.error(message)

    def critical(self, message: str, **kwargs):
        """
        输出 CRITICAL 级别的日志

        Args:
            message: 日志消息
            **kwargs: 额外的上下文信息
        """
        if kwargs:
            logger.critical(message, context=kwargs)
        else:
            logger.critical(message)

    def log_performance(
        self,
        operation: str,
        duration: float,
        status: str = "success",
        **kwargs,
    ):
        """
        记录性能指标

        Args:
            operation: 操作名称
            duration: 执行时间（秒）
            status: 操作状态（success/failed）
            **kwargs: 额外的上下文信息
        """
        message = f"Performance: {operation} took {duration:.3f} seconds ({status})"
        context = {
            "type": "performance",
            "operation": operation,
            "duration": duration,
            "status": status,
            **kwargs,
        }
        logger.info(message, context=context)

    def log_health_check(
        self,
        component: str,
        status: str,
        message: str = "",
        **kwargs,
    ):
        """
        记录健康检查结果

        Args:
            component: 组件名称
            status: 状态（healthy/unhealthy/warning）
            message: 检查消息
            **kwargs: 额外的上下文信息
        """
        log_level = (
            logger.info
            if status == "healthy"
            else logger.warning if status == "warning" else logger.error
        )
        context = {
            "type": "healthcheck",
            "component": component,
            "status": status,
            "message": message,
            **kwargs,
        }
        log_level(f"Health check: {component} is {status}", context=context)

    def log_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        **kwargs,
    ):
        """
        记录告警信息

        Args:
            alert_type: 告警类型（error/performance/resource）
            severity: 严重程度（critical/warning/info）
            message: 告警消息
            **kwargs: 额外的上下文信息
        """
        log_level = (
            logger.critical
            if severity == "critical"
            else logger.warning if severity == "warning" else logger.info
        )
        context = {
            "type": "alert",
            "alert_type": alert_type,
            "severity": severity,
            **kwargs,
        }
        log_level(f"Alert [{alert_type} - {severity}]: {message}", context=context)

    def log_metric(
        self,
        name: str,
        value: Union[int, float],
        tags: Optional[Dict[str, str]] = None,
        **kwargs,
    ):
        """
        记录指标数据

        Args:
            name: 指标名称
            value: 指标值
            tags: 指标标签
            **kwargs: 额外的上下文信息
        """
        context = {
            "type": "metric",
            "metric": name,
            "value": value,
            "tags": tags or {},
            **kwargs,
        }
        logger.info(f"Metric: {name} = {value}", context=context)

    def get_log_file_path(self) -> Path:
        """
        获取日志文件路径

        Returns:
            日志文件路径
        """
        return self.log_dir / "nanobot.log"

    def get_log_dir(self) -> Path:
        """
        获取日志目录

        Returns:
            日志目录路径
        """
        return self.log_dir


# 全局日志实例
_logger_instance: Optional[StructuredLogger] = None


def get_structured_logger() -> StructuredLogger:
    """
    获取全局结构化日志器实例

    Returns:
        StructuredLogger 实例
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = StructuredLogger()
    return _logger_instance
