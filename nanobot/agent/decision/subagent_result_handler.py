"""
Subagent 结果处理程序 - 负责处理子代理返回结果的决策逻辑
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from ..loop import AgentLoop

from ..task import Task
from .models import DecisionRequest, DecisionResult, SubagentResultRequest

logger = logging.getLogger(__name__)


class SubagentResultHandler:
    """
    子代理结果处理程序

    负责处理子代理返回结果的决策逻辑，包括：
    - 结果验证
    - 任务状态更新
    - 后续行动决策
    - 错误处理
    """

    def __init__(self, agent_loop: "AgentLoop"):
        """
        初始化子代理结果处理程序

        Args:
            agent_loop: 代理循环实例
        """
        self.agent_loop = agent_loop

    async def handle_request(self, request: DecisionRequest) -> DecisionResult:
        """
        处理子代理结果决策请求

        Args:
            request: 决策请求

        Returns:
            决策结果
        """
        logger.debug(f"处理子代理结果决策请求: {request.data}")

        try:
            # 解析子代理结果请求数据
            result_request = SubagentResultRequest(**request.data)

            # 处理子代理结果
            action, action_data = await self._handle_subagent_result(result_request, request.task)

            # 返回决策结果
            return DecisionResult(
                success=True,
                action=action,
                data=action_data,
                message=f"子代理结果处理完成: {action}",
            )
        except Exception as e:
            logger.error(f"处理子代理结果请求时发生错误: {e}", exc_info=True)
            return DecisionResult(
                success=False, action="error", message=f"处理子代理结果请求时发生错误: {str(e)}"
            )

    async def _handle_subagent_result(
        self, result: SubagentResultRequest, task: Optional[Task]
    ) -> (str, Dict[str, Any]):
        """
        处理子代理结果

        Args:
            result: 子代理结果请求
            task: 关联任务

        Returns:
            (行动类型, 行动数据)
        """
        # 检查任务是否存在
        if not task:
            logger.warning(f"子代理结果没有关联任务: {result.task_id}")
            return "task_not_found", {"task_id": result.task_id}

        # 检查子代理是否成功执行
        if result.status == "success":
            return await self._handle_success(result, task)
        elif result.status == "error":
            return await self._handle_error(result, task)
        elif result.status == "cancelled":
            return await self._handle_cancelled(result, task)
        else:
            logger.warning(f"未知的子代理状态: {result.status}")
            return "unknown_status", {"status": result.status}

    async def _handle_success(
        self, result: SubagentResultRequest, task: Task
    ) -> (str, Dict[str, Any]):
        """
        处理子代理成功结果

        Args:
            result: 子代理结果请求
            task: 关联任务

        Returns:
            (行动类型, 行动数据)
        """
        logger.info(f"子代理成功完成任务: {result.task_id}")

        # 检查任务是否需要继续执行
        if task.next_step:
            return "continue_task", {
                "task_id": result.task_id,
                "next_step": task.next_step,
                "result": result.result,
            }

        # 任务完成
        return "complete_task", {
            "task_id": result.task_id,
            "result": result.result,
            "duration": result.duration,
        }

    async def _handle_error(
        self, result: SubagentResultRequest, task: Task
    ) -> (str, Dict[str, Any]):
        """
        处理子代理错误结果

        Args:
            result: 子代理结果请求
            task: 关联任务

        Returns:
            (行动类型, 行动数据)
        """
        logger.error(f"子代理执行任务失败: {result.task_id}, 错误: {result.error}")

        # 检查任务是否可以重试
        if task.retry_count < task.max_retries:
            return "retry_task", {
                "task_id": result.task_id,
                "retry_count": task.retry_count + 1,
                "error": result.error,
            }

        # 任务失败
        return "fail_task", {
            "task_id": result.task_id,
            "error": result.error,
            "duration": result.duration,
        }

    async def _handle_cancelled(
        self, result: SubagentResultRequest, task: Task
    ) -> (str, Dict[str, Any]):
        """
        处理子代理取消结果

        Args:
            result: 子代理结果请求
            task: 关联任务

        Returns:
            (行动类型, 行动数据)
        """
        logger.warning(f"子代理任务被取消: {result.task_id}")

        return "cancel_task", {"task_id": result.task_id, "reason": "子代理任务被取消"}
