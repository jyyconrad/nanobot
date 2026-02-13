"""
Cron 系统模块 - 负责定时任务调度和管理

该模块提供了 CronSystem 类，支持多种调度策略（interval, cron, once），
提供任务的添加、移除、启动和停止功能，确保线程安全。
"""

import datetime
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import schedule

# 配置日志记录
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class JobType(Enum):
    """
    任务类型枚举
    """

    INTERVAL = "interval"
    CRON = "cron"
    ONCE = "once"


@dataclass
class JobConfig:
    """
    任务配置数据类
    """

    name: str
    job_type: JobType
    schedule: Dict[str, Any]
    function: Callable
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JobStatus:
    """
    任务状态数据类
    """

    job_id: str
    name: str
    job_type: JobType
    next_run: Optional[datetime.datetime] = None
    last_run: Optional[datetime.datetime] = None
    last_success: Optional[datetime.datetime] = None
    last_failure: Optional[datetime.datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    is_running: bool = False
    error: Optional[str] = None


class CronSystem:
    """
    Cron 系统类

    负责定时任务的调度和管理，支持多种调度策略，
    提供线程安全的任务操作方法。
    """

    def __init__(self):
        """
        初始化 Cron 系统
        """
        self.logger = logger
        self.jobs: Dict[str, JobConfig] = {}
        self.schedule_jobs: Dict[str, schedule.Job] = {}
        self.status: Dict[str, JobStatus] = {}
        self.running: bool = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._stop_event = threading.Event()

    def _thread_safe(func):
        """
        线程安全装饰器
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            with self._lock:
                return func(self, *args, **kwargs)

        return wrapper

    @_thread_safe
    def add_job(self, config: JobConfig) -> str:
        """
        添加定时任务

        Args:
            config: 任务配置对象

        Returns:
            任务唯一标识符
        """
        job_id = f"job_{int(time.time() * 1000)}_{len(self.jobs)}"
        self.jobs[job_id] = config
        self.status[job_id] = JobStatus(
            job_id=job_id, name=config.name, job_type=config.job_type
        )

        # 创建调度任务
        if config.enabled:
            self._create_schedule_job(job_id, config)

        self.logger.debug(f"添加任务: {config.name} (ID: {job_id})")
        return job_id

    @_thread_safe
    def remove_job(self, job_id: str) -> bool:
        """
        移除定时任务

        Args:
            job_id: 任务唯一标识符

        Returns:
            成功移除返回 True，否则返回 False
        """
        if job_id not in self.jobs:
            return False

        # 移除调度任务
        if job_id in self.schedule_jobs:
            try:
                schedule.cancel_job(self.schedule_jobs[job_id])
                del self.schedule_jobs[job_id]
            except Exception as e:
                self.logger.error(f"移除调度任务失败: {job_id}, 错误: {e}")

        # 移除任务配置和状态
        del self.jobs[job_id]
        del self.status[job_id]

        self.logger.debug(f"移除任务: {job_id}")
        return True

    @_thread_safe
    def enable_job(self, job_id: str) -> bool:
        """
        启用任务

        Args:
            job_id: 任务唯一标识符

        Returns:
            成功启用返回 True，否则返回 False
        """
        if job_id not in self.jobs:
            return False

        config = self.jobs[job_id]
        if config.enabled:
            return True

        config.enabled = True
        self._create_schedule_job(job_id, config)
        self.logger.debug(f"启用任务: {job_id}")
        return True

    @_thread_safe
    def disable_job(self, job_id: str) -> bool:
        """
        禁用任务

        Args:
            job_id: 任务唯一标识符

        Returns:
            成功禁用返回 True，否则返回 False
        """
        if job_id not in self.jobs:
            return False

        config = self.jobs[job_id]
        if not config.enabled:
            return True

        config.enabled = False
        if job_id in self.schedule_jobs:
            try:
                schedule.cancel_job(self.schedule_jobs[job_id])
                del self.schedule_jobs[job_id]
            except Exception as e:
                self.logger.error(f"取消调度任务失败: {job_id}, 错误: {e}")

        self.logger.debug(f"禁用任务: {job_id}")
        return True

    @_thread_safe
    def start(self) -> bool:
        """
        启动调度器

        Returns:
            成功启动返回 True，否则返回 False
        """
        if self.running:
            return True

        self.running = True
        self._stop_event.clear()
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop, name="CronSchedulerThread", daemon=True
        )
        self.scheduler_thread.start()
        self.logger.info("Cron 系统启动")
        return True

    @_thread_safe
    def stop(self) -> bool:
        """
        停止调度器

        Returns:
            成功停止返回 True，否则返回 False
        """
        if not self.running:
            return True

        self.running = False
        self._stop_event.set()
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=1)
        self.logger.info("Cron 系统停止")
        return True

    def _scheduler_loop(self):
        """
        调度器循环
        """
        while self.running and not self._stop_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"调度器循环错误: {e}")
                time.sleep(1)

    def _create_schedule_job(self, job_id: str, config: JobConfig):
        """
        创建调度任务
        """
        try:
            if config.job_type == JobType.INTERVAL:
                # 间隔调度
                interval = config.schedule.get("seconds", 60)
                job = schedule.every(interval).seconds.do(self._job_wrapper, job_id)

            elif config.job_type == JobType.CRON:
                # Cron 调度
                cron_str = config.schedule.get("cron", "* * * * *")
                job = self._parse_cron_expression(cron_str).do(
                    self._job_wrapper, job_id
                )

            elif config.job_type == JobType.ONCE:
                # 一次性调度
                run_at = config.schedule.get("run_at")
                if isinstance(run_at, str):
                    run_at = datetime.datetime.fromisoformat(run_at)
                elif not isinstance(run_at, datetime.datetime):
                    raise ValueError("无效的 run_at 参数")

                delta = run_at - datetime.datetime.now()
                if delta.total_seconds() > 0:
                    job = schedule.every(delta.total_seconds()).seconds.do(
                        self._job_wrapper, job_id
                    )
                else:
                    raise ValueError("run_at 必须是未来时间")

            else:
                raise ValueError(f"不支持的任务类型: {config.job_type}")

            self.schedule_jobs[job_id] = job
            self.logger.debug(f"创建调度任务: {job_id}")

        except Exception as e:
            self.logger.error(f"创建调度任务失败: {job_id}, 错误: {e}")
            if job_id in self.status:
                self.status[job_id].error = str(e)

    def _parse_cron_expression(self, cron_str: str):
        """
        解析 Cron 表达式
        """
        parts = cron_str.strip().split()
        if len(parts) != 5:
            raise ValueError("Cron 表达式必须包含 5 个字段")

        minute, hour, day, month, weekday = parts

        job = schedule.every()

        # 处理分钟
        if minute != "*":
            job = job.at(
                f"{self._parse_time_field(hour)}:{self._parse_time_field(minute)}"
            )

        # 处理小时
        if hour != "*" and minute == "*":
            job = job.at(f"{self._parse_time_field(hour)}:00")

        # 处理日期
        if day != "*":
            # 简化实现，仅支持每天相同时间
            pass

        # 处理月份
        if month != "*":
            # 简化实现，仅支持每月相同日期
            pass

        # 处理星期
        if weekday != "*":
            # 简化实现，仅支持每周相同时间
            weekdays = {
                "0": "monday",
                "1": "tuesday",
                "2": "wednesday",
                "3": "thursday",
                "4": "friday",
                "5": "saturday",
                "6": "sunday",
            }
            if weekday in weekdays:
                job = getattr(job, weekdays[weekday])

        return job

    def _parse_time_field(self, field: str) -> str:
        """
        解析时间字段
        """
        try:
            value = int(field)
            return f"{value:02d}"
        except ValueError:
            raise ValueError(f"无效的时间字段: {field}")

    def _job_wrapper(self, job_id: str):
        """
        任务执行包装器
        """
        if job_id not in self.jobs or job_id not in self.status:
            return

        status = self.status[job_id]
        status.is_running = True
        status.run_count += 1

        start_time = time.time()
        self.logger.debug(f"任务开始执行: {job_id}")

        try:
            config = self.jobs[job_id]
            result = config.function(*config.args, **config.kwargs)
            status.last_run = datetime.datetime.now()
            status.last_success = status.last_run
            status.success_count += 1
            status.error = None
            self.logger.debug(f"任务执行成功: {job_id}")

            # 处理一次性任务
            if config.job_type == JobType.ONCE:
                self.remove_job(job_id)

        except Exception as e:
            status.last_run = datetime.datetime.now()
            status.last_failure = status.last_run
            status.failure_count += 1
            status.error = str(e)
            self.logger.error(f"任务执行失败: {job_id}, 错误: {e}")

        finally:
            status.is_running = False
            self._update_next_run(job_id)

    @_thread_safe
    def _update_next_run(self, job_id: str):
        """
        更新下次运行时间
        """
        if job_id in self.schedule_jobs:
            try:
                # 简化实现，假设下次运行时间计算
                job = self.schedule_jobs[job_id]
                # schedule 库不直接提供 next_run 属性，这里使用简单估算
                if self.jobs[job_id].job_type == JobType.INTERVAL:
                    interval = self.jobs[job_id].schedule.get("seconds", 60)
                    self.status[
                        job_id
                    ].next_run = datetime.datetime.now() + datetime.timedelta(
                        seconds=interval
                    )
            except Exception as e:
                self.logger.error(f"更新下次运行时间失败: {job_id}, 错误: {e}")

    @_thread_safe
    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """
        获取任务状态

        Args:
            job_id: 任务唯一标识符

        Returns:
            任务状态对象，不存在则返回 None
        """
        return self.status.get(job_id)

    @_thread_safe
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """
        获取所有任务信息

        Returns:
            任务信息列表
        """
        jobs_info = []
        for job_id, config in self.jobs.items():
            status = self.status.get(job_id, {})
            jobs_info.append(
                {
                    "job_id": job_id,
                    "name": config.name,
                    "job_type": config.job_type.value,
                    "schedule": config.schedule,
                    "enabled": config.enabled,
                    "metadata": config.metadata,
                    "status": {
                        "next_run": (
                            status.next_run.isoformat()
                            if hasattr(status, "next_run") and status.next_run
                            else None
                        ),
                        "last_run": (
                            status.last_run.isoformat()
                            if hasattr(status, "last_run") and status.last_run
                            else None
                        ),
                        "last_success": (
                            status.last_success.isoformat()
                            if hasattr(status, "last_success") and status.last_success
                            else None
                        ),
                        "last_failure": (
                            status.last_failure.isoformat()
                            if hasattr(status, "last_failure") and status.last_failure
                            else None
                        ),
                        "run_count": (
                            status.run_count if hasattr(status, "run_count") else 0
                        ),
                        "success_count": (
                            status.success_count
                            if hasattr(status, "success_count")
                            else 0
                        ),
                        "failure_count": (
                            status.failure_count
                            if hasattr(status, "failure_count")
                            else 0
                        ),
                        "is_running": (
                            status.is_running
                            if hasattr(status, "is_running")
                            else False
                        ),
                        "error": status.error if hasattr(status, "error") else None,
                    },
                }
            )
        return jobs_info

    @_thread_safe
    def get_job_count(self) -> Tuple[int, int, int]:
        """
        获取任务统计信息

        Returns:
            (总任务数, 启用任务数, 运行中任务数)
        """
        total = len(self.jobs)
        enabled = sum(1 for config in self.jobs.values() if config.enabled)
        running = sum(1 for status in self.status.values() if status.is_running)
        return total, enabled, running

    @_thread_safe
    def clear_all_jobs(self):
        """
        清除所有任务
        """
        # 先停止调度器
        if self.running:
            self.stop()

        # 清除所有任务
        self.jobs.clear()
        self.schedule_jobs.clear()
        self.status.clear()

        # 清除 schedule 库的任务
        schedule.clear()

        self.logger.debug("清除所有任务")

    @_thread_safe
    def is_running(self) -> bool:
        """
        检查调度器是否正在运行

        Returns:
            运行中返回 True，否则返回 False
        """
        return self.running

    @_thread_safe
    def get_next_run(self, job_id: str) -> Optional[datetime.datetime]:
        """
        获取任务的下次运行时间

        Args:
            job_id: 任务唯一标识符

        Returns:
            下次运行时间，不存在则返回 None
        """
        status = self.status.get(job_id)
        if status and status.next_run:
            return status.next_run
        return None


# 工厂函数
def create_cron_system() -> CronSystem:
    """
    创建 Cron 系统实例

    Returns:
        CronSystem 实例
    """
    return CronSystem()


# 便捷函数
def add_interval_job(
    cron: CronSystem,
    name: str,
    function: Callable,
    seconds: int = 60,
    args: Optional[List[Any]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    enabled: bool = True,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    便捷函数：添加间隔任务

    Args:
        cron: Cron 系统实例
        name: 任务名称
        function: 任务函数
        seconds: 间隔秒数
        args: 函数参数
        kwargs: 函数关键字参数
        enabled: 是否启用
        metadata: 元数据

    Returns:
        任务唯一标识符
    """
    config = JobConfig(
        name=name,
        job_type=JobType.INTERVAL,
        schedule={"seconds": seconds},
        function=function,
        args=args or [],
        kwargs=kwargs or {},
        enabled=enabled,
        metadata=metadata or {},
    )
    return cron.add_job(config)


def add_cron_job(
    cron: CronSystem,
    name: str,
    function: Callable,
    cron_str: str = "* * * * *",
    args: Optional[List[Any]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    enabled: bool = True,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    便捷函数：添加 Cron 任务

    Args:
        cron: Cron 系统实例
        name: 任务名称
        function: 任务函数
        cron_str: Cron 表达式
        args: 函数参数
        kwargs: 函数关键字参数
        enabled: 是否启用
        metadata: 元数据

    Returns:
        任务唯一标识符
    """
    config = JobConfig(
        name=name,
        job_type=JobType.CRON,
        schedule={"cron": cron_str},
        function=function,
        args=args or [],
        kwargs=kwargs or {},
        enabled=enabled,
        metadata=metadata or {},
    )
    return cron.add_job(config)


def add_once_job(
    cron: CronSystem,
    name: str,
    function: Callable,
    run_at: Union[datetime.datetime, str],
    args: Optional[List[Any]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    enabled: bool = True,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    便捷函数：添加一次性任务

    Args:
        cron: Cron 系统实例
        name: 任务名称
        function: 任务函数
        run_at: 运行时间
        args: 函数参数
        kwargs: 函数关键字参数
        enabled: 是否启用
        metadata: 元数据

    Returns:
        任务唯一标识符
    """
    if isinstance(run_at, str):
        run_at = datetime.datetime.fromisoformat(run_at)

    config = JobConfig(
        name=name,
        job_type=JobType.ONCE,
        schedule={"run_at": run_at},
        function=function,
        args=args or [],
        kwargs=kwargs or {},
        enabled=enabled,
        metadata=metadata or {},
    )
    return cron.add_job(config)
