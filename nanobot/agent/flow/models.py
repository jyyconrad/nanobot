"""
交互流程管理数据模型

包含 Flow 状态机、步骤、进度等数据模型。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, Field


class FlowState(str, Enum):
    """交互流程状态枚举"""

    INIT = "init"  # 初始化
    IN_PROGRESS = "in_progress"  # 进行中
    WAITING_INPUT = "waiting_input"  # 等待用户输入
    PAUSED = "paused"  # 暂停
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    ERROR = "error"  # 错误


class FlowStep(BaseModel):
    """流程步骤定义"""

    id: str = Field(..., description="步骤唯一标识")
    name: str = Field(..., description="步骤名称")
    description: str = Field(..., description="步骤描述")
    state: FlowState = Field(default=FlowState.INIT, description="当前状态")

    # 执行相关
    action: Optional[str] = Field(None, description="要执行的动作")
    condition: Optional[str] = Field(None, description="执行条件")
    requires_input: bool = Field(default=False, description="是否需要用户输入")

    # 依赖关系
    dependencies: List[str] = Field(default_factory=list, description="依赖的步骤ID列表")
    next_steps: List[str] = Field(default_factory=list, description="后续步骤ID列表")

    # 时间记录
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # 结果
    output: Any = None
    error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class FlowProgress(BaseModel):
    """流程进度信息"""

    total_steps: int = Field(default=0, description="总步骤数")
    completed_steps: int = Field(default=0, description="已完成步骤数")
    current_step_id: Optional[str] = Field(None, description="当前步骤ID")
    current_step_name: Optional[str] = Field(None, description="当前步骤名称")
    percent: float = Field(default=0.0, description="完成百分比 (0-100)")

    estimated_total_time: Optional[int] = Field(None, description="预计总时间（秒）")
    elapsed_time: float = Field(default=0.0, description="已用时间（秒）")
    remaining_time: Optional[float] = Field(None, description="预计剩余时间（秒）")

    state: FlowState = Field(default=FlowState.INIT, description="整体状态")

    def calculate_percent(self) -> float:
        """计算完成百分比"""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100

    def update_percent(self) -> None:
        """更新百分比"""
        self.percent = self.calculate_percent()


class FlowResult(BaseModel):
    """流程执行结果"""

    success: bool = Field(..., description="是否成功")
    state: FlowState = Field(..., description="最终状态")
    output: Any = Field(default=None, description="输出结果")
    error: Optional[str] = Field(None, description="错误信息")

    # 执行统计
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None

    # 步骤结果
    step_results: Dict[str, Any] = Field(default_factory=dict, description="各步骤结果")

    class Config:
        arbitrary_types_allowed = True


class WizardStep(BaseModel):
    """向导步骤定义"""

    id: str = Field(..., description="步骤唯一标识")
    title: str = Field(..., description="步骤标题")
    description: str = Field(..., description="步骤描述")
    prompt: str = Field(..., description="给用户的提示")
    input_type: str = Field(default="text", description="输入类型：text, select, confirm, multiline")

    # 输入选项（用于 select 类型）
    options: List[Dict[str, str]] = Field(default_factory=list, description="选项列表")

    # 验证
    required: bool = Field(default=True, description="是否必填")
    validation_pattern: Optional[str] = Field(None, description="验证正则表达式")
    validation_message: str = Field(default="输入无效，请重新输入", description="验证失败提示")

    # 条件显示
    condition: Optional[str] = Field(None, description="显示条件")

    # 后续步骤
    next_step_id: Optional[str] = Field(None, description="下一步ID")


class WizardConfig(BaseModel):
    """向导配置"""

    id: str = Field(..., description="向导唯一标识")
    name: str = Field(..., description="向导名称")
    description: str = Field(..., description="向导描述")

    # 步骤定义
    steps: List[WizardStep] = Field(..., description="步骤列表")
    start_step_id: str = Field(..., description="起始步骤ID")

    # 选项
    allow_cancel: bool = Field(default=True, description="允许取消")
    allow_back: bool = Field(default=True, description="允许返回上一步")
    show_progress: bool = Field(default=True, description="显示进度")

    # 完成回调
    on_complete: Optional[str] = Field(None, description="完成时的回调函数路径")
    on_cancel: Optional[str] = Field(None, description="取消时的回调函数路径")


class FlowContext(BaseModel):
    """流程上下文"""

    flow_id: str = Field(..., description="流程唯一标识")
    user_id: Optional[str] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")

    # 当前状态
    current_state: FlowState = Field(default=FlowState.INIT)
    current_step_id: Optional[str] = Field(None, description="当前步骤ID")

    # 数据存储
    data: Dict[str, Any] = Field(default_factory=dict, description="流程数据")
    step_data: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="各步骤数据")

    # 历史记录
    step_history: List[str] = Field(default_factory=list, description="步骤历史")

    # 时间记录
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True

    def set_data(self, key: str, value: Any) -> None:
        """设置流程数据"""
        self.data[key] = value
        self.updated_at = datetime.now()

    def get_data(self, key: str, default: Any = None) -> Any:
        """获取流程数据"""
        return self.data.get(key, default)

    def set_step_data(self, step_id: str, key: str, value: Any) -> None:
        """设置步骤数据"""
        if step_id not in self.step_data:
            self.step_data[step_id] = {}
        self.step_data[step_id][key] = value
        self.updated_at = datetime.now()

    def get_step_data(self, step_id: str, key: str, default: Any = None) -> Any:
        """获取步骤数据"""
        return self.step_data.get(step_id, {}).get(key, default)


# 类型变量
T = TypeVar("T")
