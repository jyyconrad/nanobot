"""
任务数据模型
============

定义 Nanobot 任务管理系统的核心数据结构。
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"       # 待执行
    RUNNING = "running"       # 执行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消
    PAUSED = "paused"         # 暂停


@dataclass
class Task:
    """任务数据模型"""
    # 任务唯一标识
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # 任务类型（用于路由和处理）
    type: str = "general"

    # 任务状态
    status: TaskStatus = TaskStatus.PENDING

    # 原始消息（触发任务的输入）
    original_message: str = ""

    # 当前任务描述
    current_task: str = ""

    # 执行进度（0-100）
    progress: float = 0.0

    # 关联的子代理ID
    subagent_id: str = ""

    # 会话密钥（用于关联上下文）
    session_key: str = ""

    # 消息渠道（如：telegram, discord, wechat等）
    channel: str = ""

    # 聊天ID（渠道内的唯一标识）
    chat_id: str = ""

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    # 任务结果
    result: Optional[str] = None

    # 任务历史记录
    history: List[str] = field(default_factory=list)

    # 额外信息
    metadata: dict = field(default_factory=dict)

    def update_progress(self, progress: float, message: str = ""):
        """更新任务进度"""
        self.progress = max(0.0, min(100.0, progress))
        self.updated_at = datetime.now()
        if message:
            self.history.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def mark_completed(self, result: str = ""):
        """标记任务完成"""
        self.status = TaskStatus.COMPLETED
        self.progress = 100.0
        self.result = result
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
        self.history.append(f"[{datetime.now().strftime('%H:%M:%S')}] 任务完成")

    def mark_failed(self, error: str):
        """标记任务失败"""
        self.status = TaskStatus.FAILED
        self.result = error
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
        self.history.append(f"[{datetime.now().strftime('%H:%M:%S')}] 任务失败: {error}")

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status.value,
            "original_message": self.original_message,
            "current_task": self.current_task,
            "progress": self.progress,
            "subagent_id": self.subagent_id,
            "session_key": self.session_key,
            "channel": self.channel,
            "chat_id": self.chat_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "history": self.history,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """从字典创建任务对象"""
        task = cls(
            id=data.get("id", str(uuid.uuid4())),
            type=data.get("type", "general"),
            original_message=data.get("original_message", ""),
            current_task=data.get("current_task", ""),
            progress=data.get("progress", 0.0),
            subagent_id=data.get("subagent_id", ""),
            session_key=data.get("session_key", ""),
            channel=data.get("channel", ""),
            chat_id=data.get("chat_id", ""),
            result=data.get("result"),
            history=data.get("history", []),
            metadata=data.get("metadata", {})
        )

        task.status = TaskStatus(data.get("status", "pending"))

        if "created_at" in data:
            task.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            task.updated_at = datetime.fromisoformat(data["updated_at"])
        if "completed_at" in data and data["completed_at"]:
            task.completed_at = datetime.fromisoformat(data["completed_at"])

        return task
