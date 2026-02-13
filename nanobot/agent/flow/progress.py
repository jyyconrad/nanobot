"""
进度追踪器

提供多步骤向导的进度提示和可视化功能。
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

from loguru import logger

from .models import FlowProgress, FlowState, FlowStep, WizardStep


class ProgressFormatter:
    """进度格式化器"""

    # 进度条字符
    FILLED_CHAR = "█"
    EMPTY_CHAR = "░"
    ARROW_CHAR = "▶"
    CHECK_CHAR = "✓"
    CROSS_CHAR = "✗"
    DOT_CHAR = "○"

    @classmethod
    def format_progress_bar(
        cls,
        percent: float,
        width: int = 20,
        show_percent: bool = True,
    ) -> str:
        """
        格式化进度条

        Args:
            percent: 百分比 (0-100)
            width: 进度条宽度
            show_percent: 是否显示百分比

        Returns:
            格式化后的进度条字符串
        """
        filled = int(width * percent / 100)
        empty = width - filled

        bar = cls.FILLED_CHAR * filled + cls.EMPTY_CHAR * empty

        if show_percent:
            return f"[{bar}] {percent:.1f}%"
        return f"[{bar}]"

    @classmethod
    def format_step_list(
        cls,
        steps: List[Union[FlowStep, WizardStep]],
        current_step_id: Optional[str] = None,
        show_description: bool = False,
    ) -> str:
        """
        格式化步骤列表

        Args:
            steps: 步骤列表
            current_step_id: 当前步骤ID
            show_description: 是否显示描述

        Returns:
            格式化后的步骤列表字符串
        """
        lines = []

        for i, step in enumerate(steps, 1):
            # 确定状态图标
            if hasattr(step, "state"):
                # FlowStep
                state = step.state
                if state == FlowState.COMPLETED:
                    icon = cls.CHECK_CHAR
                elif state == FlowState.ERROR:
                    icon = cls.CROSS_CHAR
                elif step.id == current_step_id:
                    icon = cls.ARROW_CHAR
                else:
                    icon = cls.DOT_CHAR
            else:
                # WizardStep
                if step.id == current_step_id:
                    icon = cls.ARROW_CHAR
                else:
                    icon = cls.DOT_CHAR

            # 构建行
            line = f"{icon} {i}. {step.name if hasattr(step, 'name') else step.title}"
            lines.append(line)

            # 添加描述
            if show_description and step.description:
                lines.append(f"   {step.description}")

        return "\n".join(lines)

    @classmethod
    def format_time_estimate(
        cls,
        elapsed: float,
        remaining: Optional[float] = None,
    ) -> str:
        """
        格式化时间估计

        Args:
            elapsed: 已用时间（秒）
            remaining: 预计剩余时间（秒）

        Returns:
            格式化后的时间字符串
        """

        def format_duration(seconds: float) -> str:
            if seconds < 60:
                return f"{int(seconds)}秒"
            elif seconds < 3600:
                return f"{int(seconds / 60)}分钟"
            else:
                hours = int(seconds / 3600)
                minutes = int((seconds % 3600) / 60)
                return f"{hours}小时{minutes}分钟"

        parts = [f"已用: {format_duration(elapsed)}"]

        if remaining is not None:
            parts.append(f"预计剩余: {format_duration(remaining)}")

        return " | ".join(parts)


class ProgressTracker:
    """
    进度追踪器

    提供实时的进度更新和通知功能。
    """

    def __init__(
        self,
        flow_id: str,
        total_steps: int,
        on_progress: Optional[Callable[[FlowProgress], None]] = None,
    ):
        """
        初始化进度追踪器

        Args:
            flow_id: 流程ID
            total_steps: 总步骤数
            on_progress: 进度更新回调
        """
        self.flow_id = flow_id
        self.total_steps = total_steps
        self.on_progress = on_progress
        self._completed_steps = 0
        self._current_step_id: Optional[str] = None
        self._current_step_name: Optional[str] = None
        self._start_time = datetime.now()
        self._state = FlowState.INIT

    def start(
        self, first_step_id: Optional[str] = None, first_step_name: Optional[str] = None
    ):
        """
        开始追踪

        Args:
            first_step_id: 第一步ID
            first_step_name: 第一步名称
        """
        self._start_time = datetime.now()
        self._state = FlowState.IN_PROGRESS
        self._current_step_id = first_step_id
        self._current_step_name = first_step_name
        self._notify()

    def step_completed(self, step_id: str, output: Any = None):
        """
        标记步骤完成

        Args:
            step_id: 步骤ID
            output: 输出结果
        """
        self._completed_steps += 1
        logger.debug(f"步骤完成: flow_id={self.flow_id}, step_id={step_id}")
        self._notify()

    def step_started(self, step_id: str, step_name: str):
        """
        标记步骤开始

        Args:
            step_id: 步骤ID
            step_name: 步骤名称
        """
        self._current_step_id = step_id
        self._current_step_name = step_name
        logger.debug(f"步骤开始: flow_id={self.flow_id}, step_id={step_id}")
        self._notify()

    def finish(self, state: FlowState = FlowState.COMPLETED):
        """
        完成追踪

        Args:
            state: 最终状态
        """
        self._state = state
        if state == FlowState.COMPLETED:
            self._completed_steps = self.total_steps
        self._notify()

    def get_progress(self) -> FlowProgress:
        """
        获取当前进度

        Returns:
            进度信息
        """
        elapsed = (datetime.now() - self._start_time).total_seconds()
        percent = 0.0

        if self.total_steps > 0:
            percent = (self._completed_steps / self.total_steps) * 100

        remaining = None
        if percent > 0 and percent < 100:
            total_estimated = elapsed / (percent / 100)
            remaining = total_estimated - elapsed

        return FlowProgress(
            total_steps=self.total_steps,
            completed_steps=self._completed_steps,
            current_step_id=self._current_step_id,
            current_step_name=self._current_step_name,
            percent=percent,
            elapsed_time=elapsed,
            remaining_time=remaining,
            state=self._state,
        )

    def format_progress_bar(self, width: int = 20) -> str:
        """
        格式化进度条

        Args:
            width: 进度条宽度

        Returns:
            进度条字符串
        """
        progress = self.get_progress()
        return ProgressFormatter.format_progress_bar(progress.percent, width)

    def _notify(self):
        """触发进度更新通知"""
        if self.on_progress:
            try:
                progress = self.get_progress()
                self.on_progress(progress)
            except Exception as e:
                logger.error(f"进度回调执行失败: {e}")


class WizardRunner:
    """
    向导运行器

    执行向导配置的步骤序列。
    """

    def __init__(
        self,
        wizard: Wizard,
        flow_id: str,
        context: FlowContext,
    ):
        """
        初始化向导运行器

        Args:
            wizard: 向导实例
            flow_id: 流程ID
            context: 流程上下文
        """
        self.wizard = wizard
        self.flow_id = flow_id
        self.context = context
        self._current_step_id: Optional[str] = None
        self._completed = False
        self._cancelled = False

    async def run(self) -> FlowResult:
        """
        运行向导

        Returns:
            执行结果
        """
        start_time = datetime.now()
        self._current_step_id = self.wizard.config.start_step_id

        try:
            while self._current_step_id and not self._cancelled:
                step = self.wizard.get_step(self._current_step_id)
                if not step:
                    raise WizardStepError(f"步骤不存在: {self._current_step_id}")

                # 执行步骤
                result = await self._execute_step(step)

                if self._cancelled:
                    break

                # 确定下一步
                self._current_step_id = self._determine_next_step(step, result)

            # 构建结果
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if self._cancelled:
                return FlowResult(
                    success=False,
                    state=FlowState.CANCELLED,
                    output=None,
                    error="用户取消",
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                )

            return FlowResult(
                success=True,
                state=FlowState.COMPLETED,
                output=self.context.data,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
            )

        except Exception as e:
            logger.error(f"向导执行失败: {e}")
            end_time = datetime.now()

            return FlowResult(
                success=False,
                state=FlowState.ERROR,
                output=None,
                error=str(e),
                start_time=start_time,
                end_time=end_time,
                duration=(end_time - start_time).total_seconds(),
            )

    async def _execute_step(self, step: WizardStep) -> Any:
        """
        执行单个步骤

        Args:
            step: 步骤定义

        Returns:
            执行结果
        """
        # 记录当前步骤
        self.context.current_step_id = step.id
        self.context.step_history.append(step.id)

        # 调用步骤处理器（如果已注册）
        handler = self.wizard._step_handlers.get(step.id)
        if handler:
            try:
                result = await handler(self.context)
                # 存储结果
                self.context.set_step_data(step.id, "result", result)
                return result
            except Exception as e:
                logger.error(f"步骤处理器执行失败: step={step.id}, error={e}")
                raise

        # 默认行为：等待用户输入
        return None

    def _determine_next_step(
        self, current_step: WizardStep, result: Any
    ) -> Optional[str]:
        """
        确定下一步骤

        Args:
            current_step: 当前步骤
            result: 当前步骤结果

        Returns:
            下一步骤ID，如果没有下一步返回 None
        """
        # 如果有明确的下一步
        if current_step.next_step_id:
            return current_step.next_step_id

        # 根据条件查找下一步
        for step in self.wizard.config.steps:
            if step.id == current_step.id:
                continue
            if step.condition:
                if self.wizard._evaluate_condition(step.condition, self.context):
                    return step.id

        # 查找列表中的下一个步骤
        step_ids = [s.id for s in self.wizard.config.steps]
        try:
            current_idx = step_ids.index(current_step.id)
            if current_idx + 1 < len(step_ids):
                return step_ids[current_idx + 1]
        except ValueError:
            pass

        return None

    def cancel(self) -> None:
        """取消向导执行"""
        self._cancelled = True
        logger.info(f"向导已取消: flow_id={self.flow_id}")

    def is_completed(self) -> bool:
        """是否已完成"""
        return self._completed

    def is_cancelled(self) -> bool:
        """是否已取消"""
        return self._cancelled
