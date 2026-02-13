"""
多步骤向导系统

提供交互式多步骤向导功能，引导用户完成复杂任务。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union

from loguru import logger

from .models import FlowContext, FlowResult, FlowState, WizardConfig, WizardStep


class WizardError(Exception):
    """向导错误"""

    pass


class WizardStepError(WizardError):
    """向导步骤错误"""

    pass


class Wizard:
    """
    多步骤向导

    管理交互式多步骤向导的执行，支持条件跳转、输入验证和进度跟踪。
    """

    def __init__(
        self,
        config: WizardConfig,
        flow_manager: Optional[Any] = None,
    ):
        """
        初始化向导

        Args:
            config: 向导配置
            flow_manager: 流程管理器实例（可选）
        """
        self.config = config
        self.flow_manager = flow_manager
        self._steps_map: Dict[str, WizardStep] = {
            step.id: step for step in config.steps
        }

        # 步骤处理器
        self._step_handlers: Dict[str, Callable] = {}
        self._validators: Dict[str, Callable] = {}

        # 结果存储
        self._results: Dict[str, Any] = {}

        logger.info(f"向导初始化完成: {config.id} ({config.name})")

    def get_step(self, step_id: str) -> Optional[WizardStep]:
        """
        获取步骤定义

        Args:
            step_id: 步骤ID

        Returns:
            步骤定义，不存在返回 None
        """
        return self._steps_map.get(step_id)

    def get_start_step(self) -> WizardStep:
        """
        获取起始步骤

        Returns:
            起始步骤定义

        Raises:
            WizardError: 起始步骤不存在
        """
        step = self._steps_map.get(self.config.start_step_id)
        if not step:
            raise WizardError(f"起始步骤不存在: {self.config.start_step_id}")
        return step

    def get_next_step(
        self,
        current_step_id: str,
        context: FlowContext,
    ) -> Optional[WizardStep]:
        """
        获取下一步骤

        Args:
            current_step_id: 当前步骤ID
            context: 流程上下文

        Returns:
            下一步骤，如果没有后续步骤返回 None
        """
        current_step = self._steps_map.get(current_step_id)
        if not current_step:
            return None

        # 如果有明确的下一步ID
        if current_step.next_step_id:
            return self._steps_map.get(current_step.next_step_id)

        # 根据条件查找下一步
        for step_id, step in self._steps_map.items():
            if step_id == current_step_id:
                continue
            # 检查条件
            if step.condition:
                # 简单条件评估（可以扩展为更复杂的表达式）
                if self._evaluate_condition(step.condition, context):
                    return step
            else:
                # 找到第一个没有条件且不是当前步骤的步骤
                # 这里简化处理，实际应根据流程图结构确定
                pass

        return None

    def _evaluate_condition(self, condition: str, context: FlowContext) -> bool:
        """
        评估条件表达式

        Args:
            condition: 条件表达式
            context: 流程上下文

        Returns:
            条件是否成立
        """
        # 简单实现：支持 data.key == value 格式的条件
        try:
            if "==" in condition:
                left, right = condition.split("==", 1)
                left = left.strip()
                right = right.strip().strip("'\"")

                if left.startswith("data."):
                    key = left[5:]
                    value = context.get_data(key)
                    return str(value) == right

            # 支持 has(data.key) 格式
            if condition.startswith("has(") and condition.endswith(")"):
                key = condition[4:-1]
                if key.startswith("data."):
                    key = key[5:]
                return context.get_data(key) is not None

        except Exception as e:
            logger.warning(f"条件评估失败: {condition}, error={e}")

        return False

    def register_step_handler(
        self,
        step_id: str,
        handler: Callable[[FlowContext], Any],
    ) -> None:
        """
        注册步骤处理器

        Args:
            step_id: 步骤ID
            handler: 处理函数
        """
        self._step_handlers[step_id] = handler

    def register_validator(
        self,
        step_id: str,
        validator: Callable[[Any], Union[bool, str]],
    ) -> None:
        """
        注册输入验证器

        Args:
            step_id: 步骤ID
            validator: 验证函数，返回 True 表示通过，或返回错误信息
        """
        self._validators[step_id] = validator

    def validate_input(
        self, step_id: str, input_value: Any
    ) -> tuple[bool, Optional[str]]:
        """
        验证输入

        Args:
            step_id: 步骤ID
            input_value: 输入值

        Returns:
            (是否通过, 错误信息)
        """
        step = self._steps_map.get(step_id)
        if not step:
            return False, f"步骤不存在: {step_id}"

        # 检查必填
        if step.required and (input_value is None or input_value == ""):
            return False, "此项为必填项"

        # 执行自定义验证
        validator = self._validators.get(step_id)
        if validator:
            try:
                result = validator(input_value)
                if result is True:
                    return True, None
                elif result is False:
                    return False, step.validation_message
                else:
                    return False, str(result)
            except Exception as e:
                return False, f"验证失败: {e}"

        return True, None

    def get_progress(self) -> float:
        """
        获取当前进度百分比

        Returns:
            进度百分比 (0-100)
        """
        total = len(self.config.steps)
        if total == 0:
            return 100.0

        # 计算已完成步骤数
        # 这里简化处理，实际应根据执行状态计算
        completed = len(self._results)
        return (completed / total) * 100

    def get_step_count(self) -> int:
        """
        获取步骤总数

        Returns:
            步骤总数
        """
        return len(self.config.steps)

    def get_remaining_steps(self, current_step_id: str) -> int:
        """
        获取剩余步骤数

        Args:
            current_step_id: 当前步骤ID

        Returns:
            剩余步骤数
        """
        step_ids = [s.id for s in self.config.steps]
        try:
            current_idx = step_ids.index(current_step_id)
            return len(step_ids) - current_idx - 1
        except ValueError:
            return 0

    def is_first_step(self, step_id: str) -> bool:
        """
        检查是否为第一步

        Args:
            step_id: 步骤ID

        Returns:
            是否为第一步
        """
        return step_id == self.config.start_step_id

    def is_last_step(self, step_id: str) -> bool:
        """
        检查是否为最后一步

        Args:
            step_id: 步骤ID

        Returns:
            是否为最后一步
        """
        step = self._steps_map.get(step_id)
        if not step:
            return False

        # 如果没有明确的下一步，且没有条件跳转，则是最后一步
        if not step.next_step_id:
            # 检查是否有条件步骤
            for s in self.config.steps:
                if s.condition and s.id != step_id:
                    return False
            return True

        return False

    def can_go_back(self, current_step_id: str, context: FlowContext) -> bool:
        """
        检查是否可以返回上一步

        Args:
            current_step_id: 当前步骤ID
            context: 流程上下文

        Returns:
            是否可以返回
        """
        if not self.config.allow_back:
            return False

        # 检查是否有历史记录
        if not context.step_history:
            return False

        # 第一步不能返回
        if self.is_first_step(current_step_id):
            return False

        return True

    def get_previous_step(
        self,
        current_step_id: str,
        context: FlowContext,
    ) -> Optional[WizardStep]:
        """
        获取上一步

        Args:
            current_step_id: 当前步骤ID
            context: 流程上下文

        Returns:
            上一步骤，如果没有返回 None
        """
        if not context.step_history:
            return None

        # 从历史记录中查找上一步
        try:
            current_idx = context.step_history.index(current_step_id)
            if current_idx > 0:
                prev_step_id = context.step_history[current_idx - 1]
                return self._steps_map.get(prev_step_id)
        except ValueError:
            pass

        return None
