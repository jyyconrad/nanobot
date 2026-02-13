"""
交互流程管理器

管理用户交互状态机，提供流程控制和状态跟踪。
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Union

from loguru import logger

from .models import (
    FlowContext,
    FlowProgress,
    FlowResult,
    FlowState,
    FlowStep,
)


class FlowError(Exception):
    """流程错误"""
    pass


class FlowNotFoundError(FlowError):
    """流程未找到错误"""
    pass


class FlowInvalidStateError(FlowError):
    """流程状态无效错误"""
    pass


class FlowManager:
    """
    交互流程管理器

    管理用户交互状态机，支持多步骤流程的创建、执行和监控。
    """

    # 有效的状态转换映射
    VALID_TRANSITIONS: Dict[FlowState, Set[FlowState]] = {
        FlowState.INIT: {
            FlowState.IN_PROGRESS,
            FlowState.CANCELLED,
            FlowState.ERROR,
        },
        FlowState.IN_PROGRESS: {
            FlowState.WAITING_INPUT,
            FlowState.PAUSED,
            FlowState.COMPLETED,
            FlowState.CANCELLED,
            FlowState.ERROR,
        },
        FlowState.WAITING_INPUT: {
            FlowState.IN_PROGRESS,
            FlowState.CANCELLED,
            FlowState.ERROR,
        },
        FlowState.PAUSED: {
            FlowState.IN_PROGRESS,
            FlowState.CANCELLED,
            FlowState.ERROR,
        },
        FlowState.COMPLETED: set(),  # 终态
        FlowState.CANCELLED: set(),  # 终态
        FlowState.ERROR: {FlowState.INIT, FlowState.IN_PROGRESS},  # 可重试
    }

    def __init__(self):
        """初始化流程管理器"""
        # 存储所有流程
        self._flows: Dict[str, FlowContext] = {}
        # 存储流程步骤定义
        self._flow_steps: Dict[str, List[FlowStep]] = {}
        # 存储步骤执行函数
        self._step_handlers: Dict[str, Dict[str, Callable]] = {}
        # 状态变更回调
        self._state_callbacks: Dict[str, List[Callable]] = {}
        # 锁，用于并发控制
        self._locks: Dict[str, asyncio.Lock] = {}

        logger.info("FlowManager 初始化完成")

    def create_flow(
        self,
        steps: List[FlowStep],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        initial_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        创建新流程

        Args:
            steps: 流程步骤列表
            user_id: 用户ID
            session_id: 会话ID
            initial_data: 初始数据

        Returns:
            流程ID
        """
        flow_id = str(uuid.uuid4())

        # 创建流程上下文
        context = FlowContext(
            flow_id=flow_id,
            user_id=user_id,
            session_id=session_id,
            current_state=FlowState.INIT,
            data=initial_data or {},
        )

        # 存储流程
        self._flows[flow_id] = context
        self._flow_steps[flow_id] = steps
        self._step_handlers[flow_id] = {}
        self._state_callbacks[flow_id] = []
        self._locks[flow_id] = asyncio.Lock()

        logger.info(f"创建流程: flow_id={flow_id}, steps={len(steps)}")
        return flow_id

    def get_flow(self, flow_id: str) -> Optional[FlowContext]:
        """
        获取流程上下文

        Args:
            flow_id: 流程ID

        Returns:
            流程上下文，如果不存在返回 None
        """
        return self._flows.get(flow_id)

    def get_flow_steps(self, flow_id: str) -> List[FlowStep]:
        """
        获取流程步骤列表

        Args:
            flow_id: 流程ID

        Returns:
            步骤列表
        """
        return self._flow_steps.get(flow_id, [])

    async def transition(
        self,
        flow_id: str,
        new_state: FlowState,
        reason: Optional[str] = None,
    ) -> FlowContext:
        """
        转换流程状态

        Args:
            flow_id: 流程ID
            new_state: 新状态
            reason: 状态变更原因

        Returns:
            更新后的流程上下文

        Raises:
            FlowNotFoundError: 流程不存在
            FlowInvalidStateError: 无效的状态转换
        """
        if flow_id not in self._flows:
            raise FlowNotFoundError(f"流程不存在: {flow_id}")

        async with self._locks[flow_id]:
            flow = self._flows[flow_id]
            current_state = flow.current_state

            # 验证状态转换
            if not self._is_valid_transition(current_state, new_state):
                raise FlowInvalidStateError(
                    f"无效的状态转换: {current_state.value} -> {new_state.value}"
                )

            # 更新状态
            old_state = flow.current_state
            flow.current_state = new_state
            flow.updated_at = datetime.now()

            # 记录状态历史
            flow.step_history.append(
                f"{old_state.value} -> {new_state.value}"
                + (f" ({reason})" if reason else "")
            )

            logger.info(
                f"流程状态变更: flow_id={flow_id}, "
                f"{old_state.value} -> {new_state.value}"
            )

            # 触发回调
            await self._trigger_state_callbacks(flow_id, old_state, new_state, reason)

            return flow

    def _is_valid_transition(self, current: FlowState, new: FlowState) -> bool:
        """
        检查状态转换是否有效

        Args:
            current: 当前状态
            new: 新状态

        Returns:
            是否有效
        """
        # 相同状态总是允许
        if current == new:
            return True

        # 检查有效转换
        valid_states = self.VALID_TRANSITIONS.get(current, set())
        return new in valid_states

    def register_state_callback(
        self,
        flow_id: str,
        callback: Callable[[FlowContext, FlowState, FlowState, Optional[str]], Any],
    ) -> None:
        """
        注册状态变更回调

        Args:
            flow_id: 流程ID
            callback: 回调函数 (flow, old_state, new_state, reason) -> None
        """
        if flow_id not in self._state_callbacks:
            self._state_callbacks[flow_id] = []
        self._state_callbacks[flow_id].append(callback)

    async def _trigger_state_callbacks(
        self,
        flow_id: str,
        old_state: FlowState,
        new_state: FlowState,
        reason: Optional[str],
    ) -> None:
        """
        触发状态变更回调

        Args:
            flow_id: 流程ID
            old_state: 旧状态
            new_state: 新状态
            reason: 变更原因
        """
        callbacks = self._state_callbacks.get(flow_id, [])
        flow = self._flows.get(flow_id)

        if not flow:
            return

        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(flow, old_state, new_state, reason)
                else:
                    callback(flow, old_state, new_state, reason)
            except Exception as e:
                logger.error(f"状态回调执行失败: {e}")

    def delete_flow(self, flow_id: str) -> bool:
        """
        删除流程

        Args:
            flow_id: 流程ID

        Returns:
            是否删除成功
        """
        if flow_id not in self._flows:
            return False

        del self._flows[flow_id]
        del self._flow_steps[flow_id]
        del self._step_handlers[flow_id]
        del self._state_callbacks[flow_id]
        del self._locks[flow_id]

        logger.info(f"删除流程: {flow_id}")
        return True

    def list_flows(
        self,
        user_id: Optional[str] = None,
        state: Optional[FlowState] = None,
    ) -> List[FlowContext]:
        """
        列出流程

        Args:
            user_id: 用户ID过滤
            state: 状态过滤

        Returns:
            流程列表
        """
        flows = list(self._flows.values())

        if user_id:
            flows = [f for f in flows if f.user_id == user_id]

        if state:
            flows = [f for f in flows if f.current_state == state]

        return flows

    async def cancel_flow(self, flow_id: str, reason: Optional[str] = None) -> FlowContext:
        """
        取消流程

        Args:
            flow_id: 流程ID
            reason: 取消原因

        Returns:
            更新后的流程上下文
        """
        return await self.transition(flow_id, FlowState.CANCELLED, reason)

    async def complete_flow(
        self,
        flow_id: str,
        output: Any = None,
    ) -> FlowContext:
        """
        完成流程

        Args:
            flow_id: 流程ID
            output: 输出结果

        Returns:
            更新后的流程上下文
        """
        flow = await self.transition(flow_id, FlowState.COMPLETED)

        # 设置完成时间
        flow.completed_at = datetime.now()
        flow.data["__output"] = output

        return flow
