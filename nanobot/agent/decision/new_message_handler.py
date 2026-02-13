"""
新消息处理程序 - 负责处理新消息的决策逻辑
"""

import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from ..context_manager import ContextManager
    from ..loop import AgentLoop

from .models import DecisionRequest, DecisionResult, NewMessageRequest

logger = logging.getLogger(__name__)


class NewMessageHandler:
    """
    新消息处理程序

    负责处理新消息的决策逻辑，包括：
    - 消息分类
    - 意图识别
    - 任务创建决策
    - 响应策略确定
    """

    def __init__(self, agent_loop: "AgentLoop" = None):
        """
        初始化新消息处理程序

        Args:
            agent_loop: 代理循环实例（可选）
        """
        self.agent_loop = agent_loop

    def handle(self, message: str, context_manager: "ContextManager"):
        """
        处理消息（同步接口，用于测试）

        Args:
            message: 消息内容
            context_manager: 上下文管理器

        Returns:
            响应内容
        """
        # 简化的同步处理逻辑（用于测试）
        if message.strip() == "":
            raise ValueError("空消息不被允许")

        # 向上下文管理器添加用户消息
        context_manager.add_message("user", message)

        # 简单的响应生成
        if "你好" in message:
            response = "你好！我是 Nanobot，有什么可以帮你的？"
        elif "Python" in message or "函数" in message:
            response = "我可以帮你写 Python 函数。请告诉我具体需求。"
        elif "如何使用" in message:
            response = "使用方法很简单，你可以直接调用函数。"
        else:
            response = f"收到消息: {message}"

        # 向上下文管理器添加助手回复
        context_manager.add_message("assistant", response)

        return response

    async def handle_request(self, request: DecisionRequest) -> DecisionResult:
        """
        处理新消息决策请求

        Args:
            request: 决策请求

        Returns:
            决策结果
        """
        logger.debug(f"处理新消息决策请求: {request.data}")

        try:
            # 处理数据格式兼容性
            # CLI 直接发送的是 {"message": "...", "context": ...}
            # 需要转换为 NewMessageRequest 格式
            if "message" in request.data and "message_id" not in request.data:
                # CLI 格式：转换为 NewMessageRequest
                import uuid

                message_request = NewMessageRequest(
                    message_id=str(uuid.uuid4()),
                    content=request.data.get("message", ""),
                    sender_id=request.context.get("sender_id", "user"),
                    timestamp=request.context.get("timestamp", 0.0)
                    or datetime.now().timestamp(),
                    conversation_id=request.context.get(
                        "conversation_id", "cli:default"
                    ),
                )
            else:
                # 标准格式：直接解析
                message_request = NewMessageRequest(**request.data)

            # 分析消息内容和上下文
            action, action_data = await self._analyze_message(
                message_request, request.context
            )

            # 返回决策结果
            return DecisionResult(
                success=True,
                action=action,
                data=action_data,
                message=f"新消息处理完成: {action}",
            )
        except Exception as e:
            logger.error(f"处理新消息请求时发生错误: {e}", exc_info=True)
            return DecisionResult(
                success=False,
                action="error",
                message=f"处理新消息请求时发生错误: {str(e)}",
            )

    async def _analyze_message(
        self, message: NewMessageRequest, context: Dict[str, Any]
    ) -> (str, Dict[str, Any]):
        """
        分析消息内容并确定处理策略

        Args:
            message: 新消息请求
            context: 上下文信息

        Returns:
            (行动类型, 行动数据)
        """
        # 简化的消息分析逻辑（实际实现应更复杂）
        content = message.content.strip().lower()

        # 检查是否是取消指令
        if any(keyword in content for keyword in ["取消", "停止", "quit", "cancel"]):
            return "cancel_task", {"message_id": message.message_id}

        # 检查是否是纠正指令
        if any(
            keyword in content for keyword in ["不对", "错了", "修正", "correction"]
        ):
            return "handle_correction", {
                "message_id": message.message_id,
                "content": message.content,
            }

        # 检查是否是简单查询
        if any(keyword in content for keyword in ["?", "？", "查询", "查一下"]):
            return "simple_query", {
                "message_id": message.message_id,
                "content": message.content,
            }

        # 默认策略：创建新任务
        return "create_task", {
            "message_id": message.message_id,
            "content": message.content,
            "sender_id": message.sender_id,
            "conversation_id": message.conversation_id,
        }

    async def _should_create_task(self, message: NewMessageRequest) -> bool:
        """
        判断是否应该创建新任务

        Args:
            message: 新消息请求

        Returns:
            是否应该创建新任务
        """
        # 简化的判断逻辑
        content_length = len(message.content.strip())
        if content_length < 3:
            return False

        return True

    async def _extract_intent(self, message: NewMessageRequest) -> str:
        """
        提取消息意图

        Args:
            message: 新消息请求

        Returns:
            意图类型
        """
        # 简化的意图提取逻辑
        content = message.content.strip().lower()

        if any(keyword in content for keyword in ["帮助", "help"]):
            return "help"
        if any(keyword in content for keyword in ["查询", "查一下"]):
            return "query"
        if any(keyword in content for keyword in ["创建", "新建"]):
            return "create"
        if any(keyword in content for keyword in ["修改", "编辑"]):
            return "update"
        if any(keyword in content for keyword in ["删除", "移除"]):
            return "delete"

        return "unknown"
