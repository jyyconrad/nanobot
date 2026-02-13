"""
任务规划系统数据模型

包含所有数据模型和枚举类型，避免循环导入。
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """任务类型枚举"""

    CODE_GENERATION = "code_generation"
    TEXT_SUMMARIZATION = "text_summarization"
    DATA_ANALYSIS = "data_analysis"
    WEB_SEARCH = "web_search"
    FILE_OPERATION = "file_operation"
    SYSTEM_COMMAND = "system_command"
    OTHER = "other"


class TaskPriority(str, Enum):
    """任务优先级枚举"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStep(BaseModel):
    """任务执行步骤"""

    id: str = Field(..., description="步骤唯一标识")
    description: str = Field(..., description="步骤描述")
    expected_output: str = Field(..., description="预期输出")
    validation_criteria: str = Field(..., description="验证标准")
    dependencies: List[str] = Field(
        default_factory=list, description="依赖的步骤ID列表"
    )
    parallel: bool = Field(default=False, description="是否可以与其他步骤并行执行")
    condition: Optional[str] = Field(
        None, description="执行条件（如：if 条件成立则执行）"
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM, description="步骤优先级"
    )


class TaskPlan(BaseModel):
    """任务执行计划"""

    task_type: TaskType = Field(..., description="任务类型")
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM, description="任务优先级"
    )
    complexity: float = Field(..., description="任务复杂度评分 (0-1)")
    steps: List[TaskStep] = Field(..., description="执行步骤")
    estimated_time: int = Field(..., description="估计执行时间（秒）")
    requires_approval: bool = Field(default=False, description="是否需要用户批准")
    clarification_needed: bool = Field(default=False, description="是否需要澄清需求")
    clarification_questions: List[str] = Field(
        default_factory=list, description="澄清问题列表"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="任务依赖的外部资源或条件"
    )


class ComplexityFeature(BaseModel):
    """复杂度特征"""

    name: str = Field(..., description="特征名称")
    weight: float = Field(..., description="特征权重")
    score: float = Field(default=0.0, description="特征得分 (0-1)")


class ComplexityAnalysis(BaseModel):
    """复杂度分析结果"""

    total_score: float = Field(..., description="总得分 (0-1)")
    features: List[ComplexityFeature] = Field(..., description="各特征得分")
    explanation: str = Field(..., description="复杂度解释")


class TaskPattern(BaseModel):
    """任务模式"""

    task_type: TaskType = Field(..., description="任务类型")
    patterns: List[str] = Field(..., description="匹配模式")
    weight: float = Field(default=1.0, description="权重")


class TaskDetectionResult(BaseModel):
    """任务检测结果"""

    task_type: TaskType = Field(..., description="检测到的任务类型")
    confidence: float = Field(..., description="置信度 (0-1)")
    matched_patterns: List[str] = Field(default_factory=list, description="匹配的模式")


class Correction(BaseModel):
    """修正信息"""

    type: str = Field(..., description="修正类型")
    content: str = Field(..., description="修正内容")
    target: Optional[str] = Field(None, description="修正目标")
    confidence: float = Field(default=1.0, description="置信度 (0-1)")


class CorrectionPattern(BaseModel):
    """修正模式"""

    type: str = Field(..., description="修正类型")
    patterns: List[str] = Field(..., description="匹配模式")
    weight: float = Field(default=1.0, description="权重")


class CancellationPattern(BaseModel):
    """取消模式"""

    patterns: List[str] = Field(..., description="匹配模式")
    weight: float = Field(default=1.0, description="权重")
