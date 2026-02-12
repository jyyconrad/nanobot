"""
消息协议定义 - 用于父/子 Agent 通信

定义了 Agent 间通信的消息结构和类型。
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class MessageType(str, Enum):
    """消息类型枚举"""
    TASK_RESULT = "task_result"           # 子任务结果汇报
    STATUS_UPDATE = "status_update"       # 状态更新
    HEARTBEAT = "heartbeat"             # 心跳
    CONTROL = "control"                 # 控制命令
    ERROR = "error"                     # 错误报告
    LOG = "log"                         # 日志消息
    REQUEST = "request"                 # 请求消息
    RESPONSE = "response"               # 响应消息


class TaskResultMessage(BaseModel):
    """子任务结果消息"""
    message_type: MessageType = MessageType.TASK_RESULT
    task_id: str = Field(..., description="任务ID")
    subagent_id: str = Field(..., description="子代理ID")
    parent_agent_id: str = Field(..., description="父代理ID")
    status: str = Field(..., description="任务状态: completed, failed, cancelled")
    result: Dict[str, Any] = Field(default_factory=dict, description="任务结果数据")
    logs: List[str] = Field(default_factory=list, description="执行日志")
    execution_time: float = Field(..., description="执行时间(秒)")
    timestamp: datetime = Field(default_factory=datetime.now)


class StatusUpdateMessage(BaseModel):
    """状态更新消息"""
    message_type: MessageType = MessageType.STATUS_UPDATE
    agent_id: str = Field(..., description="代理ID")
    parent_agent_id: Optional[str] = Field(None, description="父代理ID")
    status: str = Field(..., description="状态: idle, running, paused, error")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="进度(0-1)")
    current_task: Optional[str] = Field(None, description="当前任务描述")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class ControlMessage(BaseModel):
    """控制命令消息"""
    message_type: MessageType = MessageType.CONTROL
    command: str = Field(..., description="命令: pause, resume, cancel, interrupt")
    target_agent_id: str = Field(..., description="目标代理ID")
    source_agent_id: str = Field(..., description="源代理ID")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class HeartbeatMessage(BaseModel):
    """心跳消息"""
    message_type: MessageType = MessageType.HEARTBEAT
    agent_id: str = Field(..., description="代理ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    uptime: float = Field(0.0, description="运行时间(秒)")


class ErrorMessage(BaseModel):
    """错误报告消息"""
    message_type: MessageType = MessageType.ERROR
    agent_id: str = Field(..., description="代理ID")
    error_type: str = Field(..., description="错误类型")
    error_message: str = Field(..., description="错误消息")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class LogMessage(BaseModel):
    """日志消息"""
    message_type: MessageType = MessageType.LOG
    agent_id: str = Field(..., description="代理ID")
    level: str = Field(..., description="日志级别: debug, info, warning, error")
    message: str = Field(..., description="日志消息")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class RequestMessage(BaseModel):
    """请求消息"""
    message_type: MessageType = MessageType.REQUEST
    request_id: str = Field(..., description="请求ID")
    request_type: str = Field(..., description="请求类型")
    source_agent_id: str = Field(..., description="源代理ID")
    target_agent_id: str = Field(..., description="目标代理ID")
    payload: Dict[str, Any] = Field(default_factory=dict)
    timeout: float = Field(30.0, description="超时时间(秒)")
    timestamp: datetime = Field(default_factory=datetime.now)


class ResponseMessage(BaseModel):
    """响应消息"""
    message_type: MessageType = MessageType.RESPONSE
    response_id: str = Field(..., description="响应ID")
    request_id: str = Field(..., description="对应的请求ID")
    source_agent_id: str = Field(..., description="源代理ID")
    target_agent_id: str = Field(..., description="目标代理ID")
    status: str = Field(..., description="状态: success, error, timeout")
    payload: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = Field(None, description="错误消息")
    timestamp: datetime = Field(default_factory=datetime.now)


# 消息类型映射
MESSAGE_TYPE_MAP = {
    MessageType.TASK_RESULT: TaskResultMessage,
    MessageType.STATUS_UPDATE: StatusUpdateMessage,
    MessageType.CONTROL: ControlMessage,
    MessageType.HEARTBEAT: HeartbeatMessage,
    MessageType.ERROR: ErrorMessage,
    MessageType.LOG: LogMessage,
    MessageType.REQUEST: RequestMessage,
    MessageType.RESPONSE: ResponseMessage,
}


def parse_message(data: dict) -> BaseModel:
    """
    解析消息字典为对应的消息模型

    Args:
        data: 消息字典

    Returns:
        对应的消息模型实例
    """
    message_type = data.get("message_type")

    if not message_type:
        raise ValueError("消息缺少message_type字段")

    # 获取对应的消息类
    message_class = MESSAGE_TYPE_MAP.get(message_type)

    if not message_class:
        raise ValueError(f"未知的消息类型: {message_type}")

    return message_class(**data)
