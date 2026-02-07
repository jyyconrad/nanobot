"""
配置文件加载器
==============

从配置文件加载和管理定时任务
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from nanobot.cron.types import CronAction, CronJob, CronSchedule


class CronConfigLoader:
    """
    定时任务配置加载器：从配置文件加载和管理定时任务

    支持从 JSON 文件加载定时任务配置，并提供验证和任务创建功能。
    """

    def __init__(self, config_path: str = "cron-job-config.json"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._jobs: List[CronJob] = []

    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 配置文件未找到
            json.JSONDecodeError: 配置文件格式错误
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)

        logger.info(f"Loaded cron config from {self.config_path}")
        return self._config

    def validate_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        验证配置的有效性

        Args:
            config: 配置字典，如未提供则使用已加载的配置

        Returns:
            配置是否有效
        """
        if config is None:
            config = self._config

        try:
            # 检查基本结构
            if "version" not in config:
                logger.error("Config missing 'version' field")
                return False

            if "jobs" not in config or not isinstance(config["jobs"], list):
                logger.error("Config missing 'jobs' field or it's not an array")
                return False

            # 验证每个任务
            for idx, job in enumerate(config["jobs"]):
                if not self._validate_job(job, idx):
                    return False

            logger.info("Cron config validation passed")
            return True

        except Exception as e:
            logger.error(f"Config validation failed: {e}")
            return False

    def _validate_job(self, job: Dict[str, Any], index: int) -> bool:
        """
        验证单个任务配置

        Args:
            job: 任务配置
            index: 任务索引

        Returns:
            任务配置是否有效
        """
        required_fields = ["name", "schedule", "action"]
        for field in required_fields:
            if field not in job:
                logger.error(f"Job {index} missing required field '{field}'")
                return False

        # 验证调度表达式
        if not self._validate_schedule(job["schedule"]):
            logger.error(f"Job {index} has invalid schedule: {job['schedule']}")
            return False

        # 验证动作类型
        if not self._validate_action(job["action"]):
            logger.error(f"Job {index} has invalid action: {job['action']}")
            return False

        return True

    def _validate_schedule(self, schedule: str) -> bool:
        """
        验证调度表达式（简化版Cron表达式）

        Args:
            schedule: 调度表达式

        Returns:
            表达式是否有效
        """
        try:
            # 支持基本的 Cron 格式：分 时 日 月 周
            parts = schedule.split()
            if len(parts) not in [5, 6]:
                return False

            # 简单验证每个部分的格式
            valid_chars = set("0123456789*/-,")
            for part in parts:
                for char in part:
                    if char not in valid_chars:
                        return False

            return True
        except Exception:
            return False

    def _validate_action(self, action: Dict[str, Any]) -> bool:
        """
        验证动作配置

        Args:
            action: 动作配置

        Returns:
            动作配置是否有效
        """
        required_fields = ["type"]
        for field in required_fields:
            if field not in action:
                return False

        action_type = action["type"]
        valid_types = ["trigger_agent", "monitor_status", "agent_turn"]

        if action_type not in valid_types:
            logger.error(f"Invalid action type: {action_type}")
            return False

        # 验证特定类型的动作
        if action_type == "trigger_agent":
            if "target" not in action or "method" not in action:
                logger.error("trigger_agent action missing target or method")
                return False

        elif action_type == "monitor_status":
            if "targets" not in action or not isinstance(action["targets"], list):
                logger.error("monitor_status action missing targets or invalid format")
                return False

        return True

    def create_jobs(self, config: Optional[Dict[str, Any]] = None) -> List[CronJob]:
        """
        从配置创建任务对象

        Args:
            config: 配置字典，如未提供则使用已加载的配置

        Returns:
            任务对象列表
        """
        if config is None:
            config = self._config

        if not self.validate_config(config):
            return []

        self._jobs = []

        for job_config in config["jobs"]:
            try:
                job = self._create_job_from_config(job_config)
                self._jobs.append(job)
                logger.debug(f"Created job: {job.name}")
            except Exception as e:
                logger.error(f"Failed to create job: {e}")
                continue

        logger.info(f"Created {len(self._jobs)} cron jobs from config")
        return self._jobs

    def _create_job_from_config(self, job_config: Dict[str, Any]) -> CronJob:
        """
        从任务配置创建任务对象

        Args:
            job_config: 任务配置字典

        Returns:
            任务对象
        """
        import uuid

        # 解析动作
        action = CronAction(**job_config["action"])

        # 创建任务对象
        job = CronJob(
            id=job_config.get("id", str(uuid.uuid4())[:8]),
            name=job_config["name"],
            enabled=job_config.get("enabled", True),
            schedule=self._parse_schedule(job_config["schedule"]),
            action=action,
            description=job_config.get("description"),
            tags=job_config.get("tags", []),
        )

        return job

    def _parse_schedule(self, schedule: str) -> CronSchedule:
        """
        解析调度配置

        Args:
            schedule: 调度字符串（Cron表达式）

        Returns:
            调度对象
        """
        return CronSchedule(kind="cron", expr=schedule)

    def get_jobs(self) -> List[CronJob]:
        """
        获取所有任务对象

        Returns:
            任务对象列表
        """
        return self._jobs.copy()

    def get_job_by_name(self, name: str) -> Optional[CronJob]:
        """
        根据名称获取任务对象

        Args:
            name: 任务名称

        Returns:
            任务对象，未找到则返回None
        """
        for job in self._jobs:
            if job.name == name:
                return job
        return None

    def reload_config(self) -> List[CronJob]:
        """
        重新加载配置

        Returns:
            新的任务对象列表
        """
        self._config = self.load_config()
        return self.create_jobs()

    def save_config(self, config: Dict[str, Any], path: Optional[str] = None):
        """
        保存配置到文件

        Args:
            config: 配置字典
            path: 保存路径，如未提供则使用默认路径
        """
        if path is None:
            path = str(self.config_path)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        logger.info(f"Config saved to {path}")

    def get_global_settings(self) -> Dict[str, Any]:
        """
        获取全局设置

        Returns:
            全局设置字典
        """
        return self._config.get("globalSettings", {})
