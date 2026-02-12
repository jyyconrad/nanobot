"""
Agent状态跟踪和任务进度管理模块
"""

import enum
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Any

from loguru import logger


class AgentState(enum.Enum):
    """Agent执行状态枚举"""
    INITIALIZING = "initializing"  # 初始化中
    RUNNING = "running"  # 运行中
    PAUSED = "paused"  # 暂停
    COMPLETED = "completed"  # 完成
    ERROR = "error"  # 错误


@dataclass
class TaskProgress:
    """任务执行进度数据"""
    task_id: str
    task_name: str
    percentage: float = 0.0
    current_step: int = 0
    total_steps: int = 100
    estimated_time_remaining: Optional[float] = None  # 估计剩余时间（秒）
    start_time: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    status: AgentState = AgentState.RUNNING
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update(self, percentage: float = None, current_step: int = None,
               total_steps: int = None, status: AgentState = None,
               metadata: Dict[str, Any] = None):
        """更新进度数据"""
        if percentage is not None:
            self.percentage = max(0.0, min(100.0, percentage))
        if current_step is not None:
            self.current_step = current_step
        if total_steps is not None:
            self.total_steps = total_steps
        if status is not None:
            self.status = status
        if metadata:
            self.metadata.update(metadata)

        self.last_updated = time.time()

        # 计算估计剩余时间
        elapsed = self.last_updated - self.start_time
        if self.percentage > 0:
            total = elapsed / (self.percentage / 100)
            self.estimated_time_remaining = max(0, total - elapsed)

    def get_throughput(self) -> float:
        """计算吞吐量（步骤/秒）"""
        elapsed = self.last_updated - self.start_time
        if elapsed > 0:
            return self.current_step / elapsed
        return 0.0

    def is_completed(self) -> bool:
        """检查任务是否完成"""
        return self.percentage >= 100.0 or self.status == AgentState.COMPLETED


class StateTracker:
    """Agent状态和任务进度追踪器"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self._state: AgentState = AgentState.INITIALIZING
        self._progress: Dict[str, TaskProgress] = {}
        self._state_history = []
        self._start_time = time.time()
        self._last_heartbeat = time.time()

    def set_state(self, state: AgentState, metadata: Dict[str, Any] = None):
        """设置Agent状态"""
        if self._state != state:
            logger.info(f"Agent {self.agent_id} 状态变更: {self._state.value} -> {state.value}")
            self._state = state
            self._state_history.append({
                "timestamp": time.time(),
                "state": state.value,
                "metadata": metadata or {}
            })

    def get_state(self) -> AgentState:
        """获取当前Agent状态"""
        return self._state

    def get_state_history(self) -> list:
        """获取状态变更历史"""
        return self._state_history.copy()

    def create_task_progress(self, task_id: str, task_name: str,
                            total_steps: int = 100) -> TaskProgress:
        """创建任务进度追踪"""
        progress = TaskProgress(
            task_id=task_id,
            task_name=task_name,
            total_steps=total_steps
        )
        self._progress[task_id] = progress
        logger.debug(f"任务进度追踪创建: {task_name} ({task_id})")
        return progress

    def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """获取任务进度"""
        return self._progress.get(task_id)

    def get_all_task_progress(self) -> Dict[str, TaskProgress]:
        """获取所有任务进度"""
        return self._progress.copy()

    def update_task_progress(self, task_id: str, **kwargs):
        """更新任务进度"""
        if task_id in self._progress:
            self._progress[task_id].update(**kwargs)
        else:
            logger.warning(f"任务进度追踪未找到: {task_id}")

    def complete_task(self, task_id: str):
        """标记任务完成"""
        if task_id in self._progress:
            self._progress[task_id].update(percentage=100.0, status=AgentState.COMPLETED)
            logger.debug(f"任务完成: {task_id}")

    def get_uptime(self) -> float:
        """获取Agent运行时间"""
        return time.time() - self._start_time

    def heartbeat(self):
        """发送心跳信号"""
        self._last_heartbeat = time.time()

    def get_last_heartbeat(self) -> float:
        """获取最后心跳时间"""
        return self._last_heartbeat

    def is_alive(self) -> bool:
        """检查Agent是否存活（心跳在合理范围内）"""
        return time.time() - self._last_heartbeat < 30  # 30秒内视为存活
