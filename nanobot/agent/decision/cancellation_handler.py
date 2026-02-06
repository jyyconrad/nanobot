"""
取消处理程序 - 负责处理用户取消请求的决策逻辑
"""

import logging
from typing import Any, Dict, Optional

from ..task import Task
from ..loop import AgentLoop
from .models import DecisionRequest, DecisionResult, CancellationRequest

logger = logging.getLogger(__name__)


class CancellationHandler:
    """
    取消处理程序
    
    负责处理用户取消请求的决策逻辑，包括：
    - 取消请求验证
    - 任务状态更新
    - 取消策略确定
    - 后续行动决策
    """

    def __init__(self, agent_loop: AgentLoop):
        """
        初始化取消处理程序
        
        Args:
            agent_loop: 代理循环实例
        """
        self.agent_loop = agent_loop

    async def handle_request(self, request: DecisionRequest) -> DecisionResult:
        """
        处理取消决策请求
        
        Args:
            request: 决策请求
            
        Returns:
            决策结果
        """
        logger.debug(f"处理取消决策请求: {request.data}")

        try:
            # 解析取消请求数据
            cancellation_request = CancellationRequest(**request.data)
            
            # 处理取消请求
            action, action_data = await self._handle_cancellation(cancellation_request, request.task)
            
            # 返回决策结果
            return DecisionResult(
                success=True,
                action=action,
                data=action_data,
                message=f"取消请求处理完成: {action}"
            )
        except Exception as e:
            logger.error(f"处理取消请求时发生错误: {e}", exc_info=True)
            return DecisionResult(
                success=False,
                action="error",
                message=f"处理取消请求时发生错误: {str(e)}"
            )

    async def _handle_cancellation(self, cancellation: CancellationRequest, task: Optional[Task]) -> (str, Dict[str, Any]):
        """
        处理取消请求
        
        Args:
            cancellation: 取消请求
            task: 关联任务
            
        Returns:
            (行动类型, 行动数据)
        """
        # 检查是否有直接关联的任务
        if task:
            return await self._handle_task_cancellation(cancellation, task)
        
        # 检查是否有任务ID关联
        if cancellation.task_id:
            return await self._handle_task_id_cancellation(cancellation)
        
        # 检查是否有正在运行的任务
        active_tasks = await self._get_active_tasks()
        if active_tasks:
            return await self._handle_active_tasks_cancellation(cancellation, active_tasks)
        
        # 没有任务需要取消
        return "no_tasks_to_cancel", {
            "reason": "没有正在运行的任务需要取消"
        }

    async def _handle_task_cancellation(self, cancellation: CancellationRequest, task: Task) -> (str, Dict[str, Any]):
        """
        处理任务取消请求
        
        Args:
            cancellation: 取消请求
            task: 关联任务
            
        Returns:
            (行动类型, 行动数据)
        """
        logger.info(f"处理任务取消请求: {task.id}")
        
        # 检查任务状态
        if task.status in ["completed", "failed", "cancelled"]:
            return "task_already_ended", {
                "task_id": task.id,
                "status": task.status
            }
        
        # 取消任务
        return "cancel_task", {
            "task_id": task.id,
            "reason": cancellation.cancellation_reason or "用户请求取消"
        }

    async def _handle_task_id_cancellation(self, cancellation: CancellationRequest) -> (str, Dict[str, Any]):
        """
        处理任务ID关联的取消请求
        
        Args:
            cancellation: 取消请求
            
        Returns:
            (行动类型, 行动数据)
        """
        logger.info(f"处理任务ID取消请求: {cancellation.task_id}")
        
        # 查找任务
        task = await self.agent_loop.task_manager.get_task(cancellation.task_id)
        if not task:
            return "task_not_found", {
                "task_id": cancellation.task_id
            }
        
        return await self._handle_task_cancellation(cancellation, task)

    async def _handle_active_tasks_cancellation(self, cancellation: CancellationRequest, active_tasks: list) -> (str, Dict[str, Any]):
        """
        处理正在运行的任务取消请求
        
        Args:
            cancellation: 取消请求
            active_tasks: 正在运行的任务列表
            
        Returns:
            (行动类型, 行动数据)
        """
        logger.info(f"处理正在运行的任务取消请求，找到 {len(active_tasks)} 个任务")
        
        # 如果只有一个正在运行的任务，直接取消
        if len(active_tasks) == 1:
            task = active_tasks[0]
            return await self._handle_task_cancellation(cancellation, task)
        
        # 如果有多个正在运行的任务，需要用户明确指定
        return "multiple_tasks_found", {
            "task_ids": [task.id for task in active_tasks],
            "reason": "找到多个正在运行的任务，请明确指定要取消的任务"
        }

    async def _get_active_tasks(self) -> list:
        """
        获取正在运行的任务列表
        
        Returns:
            正在运行的任务列表
        """
        all_tasks = await self.agent_loop.task_manager.get_all_tasks()
        return [task for task in all_tasks if task.status in ["running", "paused"]]

    async def _validate_cancellation_request(self, cancellation: CancellationRequest) -> bool:
        """
        验证取消请求
        
        Args:
            cancellation: 取消请求
            
        Returns:
            请求是否有效
        """
        # 简单的验证逻辑
        if cancellation.cancellation_reason and len(cancellation.cancellation_reason.strip()) < 3:
            logger.warning("取消原因描述太短")
            return False
            
        return True
