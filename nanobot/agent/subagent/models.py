"""
Subagent 数据模型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class SubagentStatus(str, Enum):
    """Subagent 状态枚举"""

    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SubagentTask(BaseModel):
    """Subagent 任务模型"""

    task_id: str = Field(default_factory=lambda: str(uuid4()), description="任务唯一标识符")
    description: str = Field(..., description="任务描述")
    config: Dict[str, Any] = Field(default_factory=dict, description="任务配置")
    agent_type: Optional[str] = Field(None, description="代理类型")
    skills: Optional[List[str]] = Field(None, description="技能列表")
    priority: int = Field(1, description="任务优先级")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    deadline: Optional[datetime] = Field(None, description="截止时间")


class SubagentState(BaseModel):
    """Subagent 状态模型"""

    task_id: str = Field(..., description="任务唯一标识符")
    status: SubagentStatus = Field(SubagentStatus.PENDING, description="状态")
    progress: float = Field(0.0, description="进度 (0-1)")
    current_step: Optional[str] = Field(None, description="当前步骤")
    error: Optional[str] = Field(None, description="错误信息")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


class SubagentResult(BaseModel):
    """Subagent 结果模型"""

    task_id: str = Field(..., description="任务唯一标识符")
    output: str = Field(..., description="任务输出")
    success: bool = Field(True, description="是否成功")
    error: Optional[str] = Field(None, description="错误信息")
    state: SubagentState = Field(..., description="任务状态")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="性能指标")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class SubagentConfig(BaseModel):
    """Subagent 配置模型"""

    agent_type: str = Field("default", description="代理类型")
    skills: List[str] = Field(default_factory=list, description="技能列表")
    max_tokens: int = Field(4096, description="最大令牌数")
    temperature: float = Field(0.7, description="温度参数")
    timeout: int = Field(300, description="超时时间 (秒)")
    retry_count: int = Field(3, description="重试次数")
    retry_delay: int = Field(10, description="重试延迟 (秒)")
    enable_streaming: bool = Field(False, description="是否启用流式输出")
    custom_params: Dict[str, Any] = Field(default_factory=dict, description="自定义参数")


class SubagentMetrics(BaseModel):
    """Subagent 性能指标模型"""

    execution_time: float = Field(0.0, description="执行时间 (秒)")
    tokens_used: int = Field(0, description="使用的令牌数")
    api_calls: int = Field(0, description="API 调用次数")
    error_count: int = Field(0, description="错误次数")
    memory_usage: float = Field(0.0, description="内存使用量 (MB)")
    cpu_usage: float = Field(0.0, description="CPU 使用率 (%)")


class SubagentPerformance(BaseModel):
    """Subagent 性能报告模型"""

    task_id: str = Field(..., description="任务唯一标识符")
    metrics: SubagentMetrics = Field(..., description="性能指标")
    success_rate: float = Field(0.0, description="成功率 (0-1)")
    avg_response_time: float = Field(0.0, description="平均响应时间 (秒)")
    resource_usage: Dict[str, float] = Field(default_factory=dict, description="资源使用情况")
