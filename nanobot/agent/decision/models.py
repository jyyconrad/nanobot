"""
决策系统数据模型 - 包含所有决策相关的数据模型类
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DecisionRequest(BaseModel):
    """决策请求数据模型"""

    request_type: str = Field(..., description="请求类型")
    data: Dict[str, Any] = Field(default_factory=dict, description="请求数据")
    task: Optional[Any] = Field(None, description="关联任务")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文信息")


class DecisionResult(BaseModel):
    """决策结果数据模型"""

    success: bool = Field(default=True, description="决策是否成功")
    action: str = Field(..., description="建议的行动")
    data: Dict[str, Any] = Field(default_factory=dict, description="结果数据")
    message: Optional[str] = Field(None, description="结果消息")


class NewMessageRequest(BaseModel):
    """新消息请求数据模型"""

    message_id: str = Field(..., description="消息ID")
    content: str = Field(..., description="消息内容")
    sender_id: str = Field(..., description="发送者ID")
    timestamp: float = Field(..., description="消息时间戳")
    conversation_id: str = Field(..., description="会话ID")
    message_type: str = Field(default="text", description="消息类型")


class SubagentResultRequest(BaseModel):
    """子代理结果请求数据模型"""

    subagent_id: str = Field(..., description="子代理ID")
    task_id: str = Field(..., description="任务ID")
    result: Dict[str, Any] = Field(..., description="子代理返回结果")
    status: str = Field(..., description="子代理状态")
    duration: float = Field(..., description="执行时间")
    error: Optional[str] = Field(None, description="错误信息")


class CorrectionRequest(BaseModel):
    """修正请求数据模型"""

    message_id: str = Field(..., description="消息ID")
    correction: str = Field(..., description="修正内容")
    original_message_id: Optional[str] = Field(None, description="原始消息ID")
    task_id: Optional[str] = Field(None, description="关联任务ID")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文信息")


class CancellationRequest(BaseModel):
    """取消请求数据模型"""

    message_id: str = Field(..., description="消息ID")
    cancellation_reason: Optional[str] = Field(None, description="取消原因")
    task_id: Optional[str] = Field(None, description="关联任务ID")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文信息")
