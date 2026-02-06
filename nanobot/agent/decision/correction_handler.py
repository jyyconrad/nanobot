"""
修正处理程序 - 负责处理用户修正请求的决策逻辑
"""

import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..loop import AgentLoop

from ..task import Task
from .models import DecisionRequest, DecisionResult, CorrectionRequest

logger = logging.getLogger(__name__)


class CorrectionHandler:
    """
    修正处理程序
    
    负责处理用户修正请求的决策逻辑，包括：
    - 修正类型识别
    - 任务状态调整
    - 修正策略确定
    - 后续行动决策
    """

    def __init__(self, agent_loop: "AgentLoop"):
        """
        初始化修正处理程序
        
        Args:
            agent_loop: 代理循环实例
        """
        self.agent_loop = agent_loop

    async def handle_request(self, request: DecisionRequest) -> DecisionResult:
        """
        处理修正决策请求
        
        Args:
            request: 决策请求
            
        Returns:
            决策结果
        """
        logger.debug(f"处理修正决策请求: {request.data}")

        try:
            # 解析修正请求数据
            correction_request = CorrectionRequest(**request.data)
            
            # 处理修正请求
            action, action_data = await self._handle_correction(correction_request, request.task)
            
            # 返回决策结果
            return DecisionResult(
                success=True,
                action=action,
                data=action_data,
                message=f"修正请求处理完成: {action}"
            )
        except Exception as e:
            logger.error(f"处理修正请求时发生错误: {e}", exc_info=True)
            return DecisionResult(
                success=False,
                action="error",
                message=f"处理修正请求时发生错误: {str(e)}"
            )

    async def _handle_correction(self, correction: CorrectionRequest, task: Optional[Task]) -> (str, Dict[str, Any]):
        """
        处理修正请求
        
        Args:
            correction: 修正请求
            task: 关联任务
            
        Returns:
            (行动类型, 行动数据)
        """
        # 检查是否有直接关联的任务
        if task:
            return await self._handle_task_correction(correction, task)
        
        # 检查是否有原始消息关联
        if correction.original_message_id:
            return await self._handle_message_correction(correction)
        
        # 一般修正处理
        return await self._handle_general_correction(correction)

    async def _handle_task_correction(self, correction: CorrectionRequest, task: Task) -> (str, Dict[str, Any]):
        """
        处理任务相关的修正请求
        
        Args:
            correction: 修正请求
            task: 关联任务
            
        Returns:
            (行动类型, 行动数据)
        """
        logger.info(f"处理任务修正请求: {task.id}")
        
        # 检查任务状态
        if task.status in ["completed", "failed", "cancelled"]:
            return "reopen_task", {
                "task_id": task.id,
                "correction": correction.correction
            }
        elif task.status in ["running", "paused"]:
            return "update_task", {
                "task_id": task.id,
                "correction": correction.correction,
                "status": task.status
            }
        else:
            return "start_task", {
                "task_id": task.id,
                "correction": correction.correction
            }

    async def _handle_message_correction(self, correction: CorrectionRequest) -> (str, Dict[str, Any]):
        """
        处理消息相关的修正请求
        
        Args:
            correction: 修正请求
            
        Returns:
            (行动类型, 行动数据)
        """
        logger.info(f"处理消息修正请求: {correction.original_message_id}")
        
        return "update_message", {
            "original_message_id": correction.original_message_id,
            "correction": correction.correction
        }

    async def _handle_general_correction(self, correction: CorrectionRequest) -> (str, Dict[str, Any]):
        """
        处理一般修正请求
        
        Args:
            correction: 修正请求
            
        Returns:
            (行动类型, 行动数据)
        """
        logger.info("处理一般修正请求")
        
        return "create_correction_task", {
            "correction": correction.correction,
            "context": correction.context
        }

    async def _analyze_correction_type(self, correction: CorrectionRequest) -> str:
        """
        分析修正类型
        
        Args:
            correction: 修正请求
            
        Returns:
            修正类型
        """
        correction_text = correction.correction.strip().lower()
        
        if any(keyword in correction_text for keyword in ["重新", "重新做", "重做"]):
            return "redo"
        if any(keyword in correction_text for keyword in ["修改", "更改"]):
            return "modify"
        if any(keyword in correction_text for keyword in ["补充", "添加"]):
            return "add"
        if any(keyword in correction_text for keyword in ["删除", "移除"]):
            return "delete"
        if any(keyword in correction_text for keyword in ["调整", "优化"]):
            return "adjust"
            
        return "general"
