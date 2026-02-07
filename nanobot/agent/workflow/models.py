"""
Workflow data models for Nanobot.
"""

from enum import Enum
from typing import Any, List, Optional


class MessageCategory(Enum):
    """Message classification categories."""

    # 对话类消息
    CHAT = "chat"  # 普通对话
    INQUIRY = "inquiry"  # 询问类消息

    # 任务管理类
    TASK_CREATE = "task_create"  # 创建任务
    TASK_STATUS = "task_status"  # 查询任务状态
    TASK_CANCEL = "task_cancel"  # 取消任务
    TASK_COMPLETE = "task_complete"  # 完成任务
    TASK_LIST = "task_list"  # 列出任务

    # 控制类消息
    CONTROL = "control"  # 控制命令
    HELP = "help"  # 帮助命令

    # 系统类消息
    UNKNOWN = "unknown"


class TaskState(Enum):
    """Task state enumeration."""

    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    PAUSED = "paused"  # 已暂停
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    FAILED = "failed"  # 失败


class WorkflowStep:
    """Data model for a workflow step."""

    def __init__(
        self,
        step_id: str,
        name: str,
        description: str,
        dependencies: List[str] = None,
        status: TaskState = TaskState.PENDING,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        output: Any = None,
        error: Optional[str] = None,
    ):
        self.step_id = step_id
        self.name = name
        self.description = description
        self.dependencies = dependencies or []
        self.status = status
        self.start_time = start_time
        self.end_time = end_time
        self.output = output
        self.error = error

    def __dict__(self):
        return {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "dependencies": self.dependencies,
            "status": self.status.value if isinstance(self.status, TaskState) else self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "output": self.output,
            "error": self.error,
        }


class WorkflowState(Enum):
    """Workflow state enumeration."""

    PLANNING = "planning"  # 规划中
    ACTIVE = "active"  # 进行中
    PAUSED = "paused"  # 已暂停
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
