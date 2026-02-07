"""Cron types with enhanced support for task management."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


@dataclass
class CronSchedule:
    """Schedule definition for a cron job."""

    kind: Literal["at", "every", "cron"]
    # For "at": timestamp in ms
    at_ms: int | None = None
    # For "every": interval in ms
    every_ms: int | None = None
    # For "cron": cron expression (e.g. "0 9 * * *")
    expr: str | None = None
    # Timezone for cron expressions
    tz: str | None = None


@dataclass
class CronAction:
    """
    Action to perform when the job runs.

    Supports multiple action types:
    - trigger_agent: 触发指定 Agent 的方法
    - monitor_status: 监听 Agent 状态并根据条件触发响应
    - agent_turn: 传统的 Agent 对话回合
    """

    type: Literal["trigger_agent", "monitor_status", "agent_turn"] = "agent_turn"
    target: Optional[str] = None  # 目标 Agent（trigger_agent 类型）
    method: Optional[str] = None  # 方法名称（trigger_agent 类型）
    params: Optional[Dict[str, Any]] = None  # 方法参数（trigger_agent 类型）
    targets: Optional[List[Dict[str, Any]]] = None  # 监听目标（monitor_status 类型）
    alert_conditions: Optional[Dict[str, Any]] = None  # 告警条件（monitor_status 类型）
    message: str = ""  # 消息内容（agent_turn 类型）
    deliver: bool = False  # 是否发送到频道（agent_turn 类型）
    channel: Optional[str] = None  # 目标频道（agent_turn 类型）
    to: Optional[str] = None  # 目标用户（agent_turn 类型）


@dataclass
class CronJobState:
    """Runtime state of a job."""

    next_run_at_ms: int | None = None
    last_run_at_ms: int | None = None
    last_status: Literal["ok", "error", "skipped"] | None = None
    last_error: str | None = None


@dataclass
class CronJob:
    """A scheduled job with enhanced configuration."""

    id: str
    name: str
    enabled: bool = True
    schedule: CronSchedule = field(default_factory=lambda: CronSchedule(kind="every"))
    action: CronAction = field(default_factory=CronAction)
    state: CronJobState = field(default_factory=CronJobState)
    created_at_ms: int = 0
    updated_at_ms: int = 0
    delete_after_run: bool = False
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class CronStore:
    """Persistent store for cron jobs."""

    version: int = 2
    jobs: list[CronJob] = field(default_factory=list)
    global_settings: Dict[str, Any] = field(default_factory=dict)
