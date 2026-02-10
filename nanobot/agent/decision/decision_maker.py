"""
执行决策管理器 - 负责协调和处理各种类型的决策请求
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from ..loop import AgentLoop

from .cancellation_handler import CancellationHandler
from .correction_handler import CorrectionHandler
from .models import DecisionRequest, DecisionResult
from .new_message_handler import NewMessageHandler
from .subagent_result_handler import SubagentResultHandler

logger = logging.getLogger(__name__)


class ExecutionDecisionMaker:
    """
    执行决策管理器

    负责处理各种类型的决策请求，并根据请求类型调用相应的处理程序
    """

    def __init__(self, agent_loop: Optional["AgentLoop"] = None):
        """
        初始化决策管理器

        Args:
            agent_loop: 代理循环实例（可选）
        """
        self.agent_loop = agent_loop
        self.handlers: Dict[str, Any] = {}
        if agent_loop:
            self.handlers = {
                "new_message": NewMessageHandler(agent_loop),
                "subagent_result": SubagentResultHandler(agent_loop),
                "correction": CorrectionHandler(agent_loop),
                "cancellation": CancellationHandler(agent_loop),
            }

    async def make_decision(self, request: DecisionRequest) -> DecisionResult:
        """
        处理决策请求

        Args:
            request: 决策请求

        Returns:
            决策结果

        Raises:
            ValueError: 如果请求类型不支持
        """
        logger.debug(f"处理决策请求: {request.request_type}")

        handler = self.handlers.get(request.request_type)
        if not handler:
            logger.error(f"不支持的决策请求类型: {request.request_type}")
            return DecisionResult(
                success=False, action="unknown", message=f"不支持的请求类型: {request.request_type}"
            )

        try:
            result = await handler.handle_request(request)
            logger.debug(f"决策请求处理完成: {request.request_type}, 结果: {result}")
            return result
        except Exception as e:
            logger.error(
                f"处理决策请求时发生错误: {request.request_type}, 错误: {e}", exc_info=True
            )
            return DecisionResult(
                success=False, action="error", message=f"处理请求时发生错误: {str(e)}"
            )

    def register_handler(self, request_type: str, handler: Any):
        """
        注册新的决策处理程序

        Args:
            request_type: 请求类型
            handler: 处理程序实例
        """
        self.handlers[request_type] = handler
        logger.debug(f"已注册决策处理程序: {request_type}")

    def get_handler(self, request_type: str) -> Optional[Any]:
        """
        获取指定类型的决策处理程序

        Args:
            request_type: 请求类型

        Returns:
            处理程序实例或 None
        """
        return self.handlers.get(request_type)

    def list_supported_request_types(self) -> list:
        """
        获取支持的决策请求类型列表

        Returns:
            支持的请求类型列表
        """
        return list(self.handlers.keys())
