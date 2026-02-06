"""
增强记忆系统数据模型 - 使用 Pydantic 定义类型安全的记忆结构

定义了记忆存储的核心数据模型，包括记忆内容、标签、时间戳等。
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Memory(BaseModel):
    """
    记忆实体 - 代表一个完整的记忆条目

    包含记忆内容、标签、时间戳和任务关联信息
    """
    id: str = Field(..., description="记忆唯一标识符")
    content: str = Field(..., description="记忆内容")
    tags: List[str] = Field(default_factory=list, description="记忆标签")
    task_id: Optional[str] = Field(None, description="关联的任务 ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="记忆创建时间")
    importance: int = Field(0, description="重要性等级 (0-10)")

    class Config:
        """Pydantic 配置"""
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MemorySearchQuery(BaseModel):
    """
    记忆搜索查询 - 定义搜索条件

    支持内容查询、标签过滤和任务关联过滤
    """
    query: str = Field(default="", description="内容搜索关键词")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    task_id: Optional[str] = Field(None, description="任务 ID 过滤")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    limit: int = Field(50, description="结果数量限制")


class MemorySearchResult(BaseModel):
    """
    记忆搜索结果 - 包含搜索结果和统计信息
    """
    total: int = Field(..., description="总结果数")
    results: List[Memory] = Field(default_factory=list, description="匹配的记忆列表")
    search_time_ms: float = Field(..., description="搜索耗时（毫秒）")


class MemoryUpdate(BaseModel):
    """
    记忆更新请求 - 定义更新操作

    支持增量更新记忆内容和标签
    """
    content: Optional[str] = Field(None, description="新内容（可选）")
    tags: Optional[List[str]] = Field(None, description="新标签（可选）")
    importance: Optional[int] = Field(None, description="新重要性等级（可选）")


class MemoryBatch(BaseModel):
    """
    记忆批次操作 - 用于批量处理记忆
    """
    memories: List[Memory] = Field(default_factory=list, description="记忆列表")
    operation: str = Field(default="add", description="操作类型：add/delete/update")
