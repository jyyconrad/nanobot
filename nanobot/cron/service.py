"""Cron service for scheduling agent tasks with enhanced configuration support."""

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

from loguru import logger

from nanobot.cron.types import CronAction, CronJob, CronJobState, CronSchedule, CronStore


def _now_ms() -> int:
    return int(time.time() * 1000)


def _compute_next_run(schedule: CronSchedule, now_ms: int) -> int | None:
    """Compute next run time in ms."""
    if schedule.kind == "at":
        return schedule.at_ms if schedule.at_ms and schedule.at_ms > now_ms else None

    if schedule.kind == "every":
        if not schedule.every_ms or schedule.every_ms <= 0:
            return None
        # Next interval from now
        return now_ms + schedule.every_ms

    if schedule.kind == "cron" and schedule.expr:
        try:
            from croniter import croniter

            cron = croniter(schedule.expr, time.time())
            next_time = cron.get_next()
            return int(next_time * 1000)
        except Exception:
            return None

    return None


class CronService:
    """Service for managing and executing scheduled jobs."""

    def __init__(
        self,
        store_path: Path,
        on_job: Callable[[CronJob], Coroutine[Any, Any, str | None]] | None = None,
    ):
        self.store_path = store_path
        self.on_job = on_job  # Callback to execute job, returns response text
        self._store: CronStore | None = None
        self._timer_task: asyncio.Task | None = None
        self._running = False

    def _load_store(self) -> CronStore:
        """Load jobs from disk."""
        if self._store:
            return self._store

        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text())
                jobs = []
                for j in data.get("jobs", []):
                    # 支持向后兼容（旧的 payload 字段）
                    if "payload" in j:
                        # 转换旧格式到新格式
                        action = CronAction(
                            type=j["payload"].get("kind", "agent_turn"),
                            message=j["payload"].get("message", ""),
                            deliver=j["payload"].get("deliver", False),
                            channel=j["payload"].get("channel"),
                            to=j["payload"].get("to"),
                        )
                    else:
                        # 使用新格式的 action 字段
                        action = CronAction(**j.get("action", {}))

                    jobs.append(
                        CronJob(
                            id=j["id"],
                            name=j["name"],
                            enabled=j.get("enabled", True),
                            schedule=CronSchedule(
                                kind=j["schedule"]["kind"],
                                at_ms=j["schedule"].get("atMs"),
                                every_ms=j["schedule"].get("everyMs"),
                                expr=j["schedule"].get("expr"),
                                tz=j["schedule"].get("tz"),
                            ),
                            action=action,
                            state=CronJobState(
                                next_run_at_ms=j.get("state", {}).get("nextRunAtMs"),
                                last_run_at_ms=j.get("state", {}).get("lastRunAtMs"),
                                last_status=j.get("state", {}).get("lastStatus"),
                                last_error=j.get("state", {}).get("lastError"),
                            ),
                            created_at_ms=j.get("createdAtMs", 0),
                            updated_at_ms=j.get("updatedAtMs", 0),
                            delete_after_run=j.get("deleteAfterRun", False),
                            description=j.get("description"),
                            tags=j.get("tags", []),
                        )
                    )

                self._store = CronStore(
                    version=data.get("version", 2),
                    jobs=jobs,
                    globalSettings=data.get("globalSettings", {}),
                )
            except Exception as e:
                logger.warning(f"Failed to load cron store: {e}")
                self._store = CronStore()
        else:
            self._store = CronStore()

        return self._store

    def _save_store(self) -> None:
        """Save jobs to disk."""
        if not self._store:
            return

        self.store_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": self._store.version,
            "globalSettings": self._store.global_settings,
            "jobs": [
                {
                    "id": j.id,
                    "name": j.name,
                    "enabled": j.enabled,
                    "schedule": {
                        "kind": j.schedule.kind,
                        "atMs": j.schedule.at_ms,
                        "everyMs": j.schedule.every_ms,
                        "expr": j.schedule.expr,
                        "tz": j.schedule.tz,
                    },
                    "action": {
                        "type": j.action.type,
                        "target": j.action.target,
                        "method": j.action.method,
                        "params": j.action.params,
                        "targets": j.action.targets,
                        "alertConditions": j.action.alertConditions,
                        "message": j.action.message,
                        "deliver": j.action.deliver,
                        "channel": j.action.channel,
                        "to": j.action.to,
                    },
                    "state": {
                        "nextRunAtMs": j.state.next_run_at_ms,
                        "lastRunAtMs": j.state.last_run_at_ms,
                        "lastStatus": j.state.last_status,
                        "lastError": j.state.last_error,
                    },
                    "createdAtMs": j.created_at_ms,
                    "updatedAtMs": j.updated_at_ms,
                    "deleteAfterRun": j.delete_after_run,
                    "description": j.description,
                    "tags": j.tags,
                }
                for j in self._store.jobs
            ],
        }

        self.store_path.write_text(json.dumps(data, indent=2))

    async def start(self) -> None:
        """Start the cron service."""
        self._running = True
        self._load_store()
        self._recompute_next_runs()
        self._save_store()
        self._arm_timer()
        logger.info(
            f"Cron service started with {len(self._store.jobs if self._store else [])} jobs"
        )

    def stop(self) -> None:
        """Stop the cron service."""
        self._running = False
        if self._timer_task:
            self._timer_task.cancel()
            self._timer_task = None

    def _recompute_next_runs(self) -> None:
        """Recompute next run times for all enabled jobs."""
        if not self._store:
            return
        now = _now_ms()
        for job in self._store.jobs:
            if job.enabled:
                job.state.next_run_at_ms = _compute_next_run(job.schedule, now)

    def _get_next_wake_ms(self) -> int | None:
        """Get the earliest next run time across all jobs."""
        if not self._store:
            return None
        times = [
            j.state.next_run_at_ms for j in self._store.jobs if j.enabled and j.state.next_run_at_ms
        ]
        return min(times) if times else None

    def _arm_timer(self) -> None:
        """Schedule the next timer tick."""
        if self._timer_task:
            self._timer_task.cancel()

        next_wake = self._get_next_wake_ms()
        if not next_wake or not self._running:
            return

        delay_ms = max(0, next_wake - _now_ms())
        delay_s = delay_ms / 1000

        async def tick():
            await asyncio.sleep(delay_s)
            if self._running:
                await self._on_timer()

        self._timer_task = asyncio.create_task(tick())

    async def _on_timer(self) -> None:
        """Handle timer tick - run due jobs."""
        if not self._store:
            return

        now = _now_ms()
        due_jobs = [
            j
            for j in self._store.jobs
            if j.enabled and j.state.next_run_at_ms and now >= j.state.next_run_at_ms
        ]

        for job in due_jobs:
            await self._execute_job(job)

        self._save_store()
        self._arm_timer()

    async def _execute_job(self, job: CronJob) -> None:
        """Execute a single job with support for enhanced action types."""
        start_ms = _now_ms()
        logger.info(f"Cron: executing job '{job.name}' ({job.id})")

        try:

            # 处理不同的动作类型
            if job.action.type == "trigger_agent":
                await self._execute_trigger_agent(job)
            elif job.action.type == "monitor_status":
                await self._execute_monitor_status(job)
            elif job.action.type == "agent_turn":
                if self.on_job:
                    await self.on_job(job)
            else:
                logger.warning(f"Unknown job action type: {job.action.type}")

            job.state.last_status = "ok"
            job.state.last_error = None
            logger.info(f"Cron: job '{job.name}' completed")

        except Exception as e:
            job.state.last_status = "error"
            job.state.last_error = str(e)
            logger.error(f"Cron: job '{job.name}' failed: {e}")

        job.state.last_run_at_ms = start_ms
        job.updated_at_ms = _now_ms()

        # Handle one-shot jobs
        if job.schedule.kind == "at":
            if job.delete_after_run:
                self._store.jobs = [j for j in self._store.jobs if j.id != job.id]
            else:
                job.enabled = False
                job.state.next_run_at_ms = None
        else:
            # Compute next run
            job.state.next_run_at_ms = _compute_next_run(job.schedule, _now_ms())

    async def _execute_trigger_agent(self, job: CronJob) -> str:
        """Execute a trigger_agent action."""
        logger.info(f"Triggering agent: {job.action.target}.{job.action.method}")

        # 检查是否有 Agent 触发器
        if hasattr(self, "_agent_trigger") and self._agent_trigger:
            result = await self._agent_trigger.trigger_agent(
                job.action.target, job.action.method, job.action.params
            )
            return str(result)
        else:
            logger.warning("Agent trigger not configured")
            return "Agent trigger not configured"

    async def _execute_monitor_status(self, job: CronJob) -> str:
        """Execute a monitor_status action."""
        logger.info("Monitoring agent status")

        # 检查是否有状态监听器
        if hasattr(self, "_status_monitor") and self._status_monitor:
            # 这里应该根据 job.action.targets 配置来执行具体的监听
            result = await self._status_monitor.monitor_agent(
                "mainAgent", checks=["high_failure_rate", "stalled_tasks"]
            )
            return str(result)
        else:
            logger.warning("Status monitor not configured")
            return "Status monitor not configured"

    # ========== Public API ==========

    def list_jobs(self, include_disabled: bool = False) -> list[CronJob]:
        """List all jobs."""
        store = self._load_store()
        jobs = store.jobs if include_disabled else [j for j in store.jobs if j.enabled]
        return sorted(jobs, key=lambda j: j.state.next_run_at_ms or float("inf"))

    def add_job(
        self,
        name: str,
        schedule: CronSchedule,
        action: Optional[CronAction] = None,
        delete_after_run: bool = False,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> CronJob:
        """Add a new job."""
        store = self._load_store()
        now = _now_ms()

        if action is None:
            action = CronAction(type="agent_turn", message="")

        job = CronJob(
            id=str(uuid.uuid4())[:8],
            name=name,
            enabled=True,
            schedule=schedule,
            action=action,
            state=CronJobState(next_run_at_ms=_compute_next_run(schedule, now)),
            created_at_ms=now,
            updated_at_ms=now,
            delete_after_run=delete_after_run,
            description=description,
            tags=tags or [],
        )

        store.jobs.append(job)
        self._save_store()
        self._arm_timer()

        logger.info(f"Cron: added job '{name}' ({job.id})")
        return job

    def add_trigger_job(
        self,
        name: str,
        schedule: CronSchedule,
        target: str,
        method: str,
        params: Optional[dict] = None,
        delete_after_run: bool = False,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> CronJob:
        """Add a trigger_agent type job."""
        action = CronAction(type="trigger_agent", target=target, method=method, params=params or {})

        return self.add_job(name, schedule, action, delete_after_run, description, tags)

    def add_monitor_job(
        self,
        name: str,
        schedule: CronSchedule,
        targets: Optional[list[dict]] = None,
        alert_conditions: Optional[dict] = None,
        delete_after_run: bool = False,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> CronJob:
        """Add a monitor_status type job."""
        action = CronAction(
            type="monitor_status", targets=targets or [], alertConditions=alert_conditions or {}
        )

        return self.add_job(name, schedule, action, delete_after_run, description, tags)

    def add_agent_turn_job(
        self,
        name: str,
        schedule: CronSchedule,
        message: str,
        deliver: bool = False,
        channel: Optional[str] = None,
        to: Optional[str] = None,
        delete_after_run: bool = False,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> CronJob:
        """Add a traditional agent_turn type job (compatibility method)."""
        action = CronAction(
            type="agent_turn", message=message, deliver=deliver, channel=channel, to=to
        )

        return self.add_job(name, schedule, action, delete_after_run, description, tags)

    def remove_job(self, job_id: str) -> bool:
        """Remove a job by ID."""
        store = self._load_store()
        before = len(store.jobs)
        store.jobs = [j for j in store.jobs if j.id != job_id]
        removed = len(store.jobs) < before

        if removed:
            self._save_store()
            self._arm_timer()
            logger.info(f"Cron: removed job {job_id}")

        return removed

    def enable_job(self, job_id: str, enabled: bool = True) -> CronJob | None:
        """Enable or disable a job."""
        store = self._load_store()
        for job in store.jobs:
            if job.id == job_id:
                job.enabled = enabled
                job.updated_at_ms = _now_ms()
                if enabled:
                    job.state.next_run_at_ms = _compute_next_run(job.schedule, _now_ms())
                else:
                    job.state.next_run_at_ms = None
                self._save_store()
                self._arm_timer()
                return job
        return None

    async def run_job(self, job_id: str, force: bool = False) -> bool:
        """Manually run a job."""
        store = self._load_store()
        for job in store.jobs:
            if job.id == job_id:
                if not force and not job.enabled:
                    return False
                await self._execute_job(job)
                self._save_store()
                self._arm_timer()
                return True
        return False

    def status(self) -> dict:
        """Get service status."""
        store = self._load_store()
        return {
            "enabled": self._running,
            "jobs": len(store.jobs),
            "next_wake_at_ms": self._get_next_wake_ms(),
            "version": self._store.version if self._store else 1,
        }

    def get_global_settings(self) -> dict:
        """Get global settings from store."""
        store = self._load_store()
        return store.global_settings

    def update_global_settings(self, settings: dict) -> None:
        """Update global settings."""
        store = self._load_store()
        store.global_settings.update(settings)
        self._save_store()

    def set_agent_trigger(self, trigger: Any) -> None:
        """Set the agent trigger for executing agent actions."""
        self._agent_trigger = trigger

    def set_status_monitor(self, monitor: Any) -> None:
        """Set the status monitor for checking agent status."""
        self._status_monitor = monitor

    async def load_config(self, config_path: Optional[Path] = None) -> int:
        """Load jobs from external config file."""
        from nanobot.cron.config_loader import CronConfigLoader

        if config_path is None:
            config_path = self.store_path

        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}")
            return 0

        try:
            loader = CronConfigLoader(str(config_path))
            config = loader.load_config()

            if not loader.validate_config(config):
                logger.warning("Config validation failed")
                return 0

            # 清除现有任务
            self._store.jobs.clear()

            # 创建新任务
            jobs = loader.create_jobs(config)

            for job in jobs:
                # 转换为内部格式
                self.add_job(
                    job.name,
                    job.schedule,
                    job.action,
                    delete_after_run=job.delete_after_run,
                    description=job.description,
                    tags=job.tags,
                )

            logger.info(f"Loaded {len(jobs)} jobs from config")
            return len(jobs)

        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return 0
