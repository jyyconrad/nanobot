"""
结构化日志记录模块
"""

import json
import time
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any
from pathlib import Path

from loguru import logger


class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self, name: str = "nanobot", log_dir: str = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        """
        初始化结构化日志记录器

        Args:
            name: 日志器名称
            log_dir: 日志目录（默认 ~/.nanobot/logs）
            max_file_size: 单个日志文件最大大小（字节）
            backup_count: 保留的备份文件数量
        """
        self.name = name
        self.log_dir = Path(log_dir) if log_dir else Path.home() / ".nanobot" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 设置根日志配置
        self._setup_logging(name, max_file_size, backup_count)

    def _setup_logging(self, name: str, max_file_size: int, backup_count: int):
        """设置日志配置"""
        # 创建文件处理器
        log_file = self.log_dir / f"{name}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding="utf-8"
        )

        # 创建控制台处理器
        console_handler = logging.StreamHandler()

        # 设置格式化器
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 获取根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    def _create_log_entry(self, level: str, message: str, **kwargs) -> str:
        """创建结构化日志条目"""
        entry = {
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "logger": self.name,
            **kwargs
        }
        return json.dumps(entry, ensure_ascii=False)

    def debug(self, message: str, **kwargs):
        """记录DEBUG级别的日志"""
        log_entry = self._create_log_entry("DEBUG", message, **kwargs)
        logger.debug(log_entry)

    def info(self, message: str, **kwargs):
        """记录INFO级别的日志"""
        log_entry = self._create_log_entry("INFO", message, **kwargs)
        logger.info(log_entry)

    def warning(self, message: str, **kwargs):
        """记录WARNING级别的日志"""
        log_entry = self._create_log_entry("WARNING", message, **kwargs)
        logger.warning(log_entry)

    def error(self, message: str, **kwargs):
        """记录ERROR级别的日志"""
        log_entry = self._create_log_entry("ERROR", message, **kwargs)
        logger.error(log_entry)

    def critical(self, message: str, **kwargs):
        """记录CRITICAL级别的日志"""
        log_entry = self._create_log_entry("CRITICAL", message, **kwargs)
        logger.critical(log_entry)

    def log_with_context(self, level: str, message: str,
                        request_id: Optional[str] = None,
                        task_id: Optional[str] = None,
                        session_id: Optional[str] = None,
                        **kwargs):
        """记录包含上下文信息的日志"""
        context = {}
        if request_id:
            context["request_id"] = request_id
        if task_id:
            context["task_id"] = task_id
        if session_id:
            context["session_id"] = session_id

        log_entry = self._create_log_entry(level, message, **context, **kwargs)

        # 根据级别记录日志
        if level == "DEBUG":
            logger.debug(log_entry)
        elif level == "INFO":
            logger.info(log_entry)
        elif level == "WARNING":
            logger.warning(log_entry)
        elif level == "ERROR":
            logger.error(log_entry)
        elif level == "CRITICAL":
            logger.critical(log_entry)
        else:
            logger.info(log_entry)

    def record_agent_state(self, agent_id: str, state: str, **kwargs):
        """记录Agent状态变更"""
        self.log_with_context("INFO", f"Agent state changed: {state}",
                           agent_id=agent_id, **kwargs)

    def record_task_progress(self, task_id: str, progress: float,
                           task_name: str = None, **kwargs):
        """记录任务进度"""
        self.log_with_context("INFO", f"Task progress: {progress:.1f}%",
                           task_id=task_id, task_name=task_name,
                           progress=progress, **kwargs)

    def record_llm_call(self, provider: str, model: str, latency: float,
                      prompt_tokens: int, completion_tokens: int,
                      cost: float = 0.0, **kwargs):
        """记录LLM调用"""
        self.log_with_context("INFO", "LLM call completed",
                           provider=provider, model=model,
                           latency=latency, prompt_tokens=prompt_tokens,
                           completion_tokens=completion_tokens, cost=cost,
                           **kwargs)

    def record_tool_use(self, tool_name: str, execution_time: float,
                      success: bool = True, **kwargs):
        """记录工具使用"""
        level = "INFO" if success else "ERROR"
        self.log_with_context(level, f"Tool {tool_name} executed",
                           tool_name=tool_name, execution_time=execution_time,
                           success=success, **kwargs)

    def get_log_path(self) -> Path:
        """获取日志文件路径"""
        return self.log_dir / f"{self.name}.log"

    def get_log_dir(self) -> Path:
        """获取日志目录"""
        return self.log_dir
