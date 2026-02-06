"""
新消息处理程序 - 负责处理新消息的决策逻辑
"""

import logging
from typing import Any, Dict, Optional

from ..task import Task
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

    def __init__(self, agent_loop: AgentLoop):
        """
        初始化新消息处理程序
        
        Args:
            agent_loop: 代理循环实例
        """
        self.agent_loop = agent_loop

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
            # 解析新消息请求数据
            message_request = NewMessageRequest(**request.data)
            
            # 分析消息内容和上下文
            action, action_data = await self._analyze_message(message_request, request.context)
            
            # 返回决策结果
            return DecisionResult(
                success=True,
                action=action,
                data=action_data,
                message=f"新消息处理完成: {action}"
            )
        except Exception as e:
            logger.error(f"处理新消息请求时发生错误: {e}", exc_info=True)
            return DecisionResult(
                success=False,
                action="error",
                message=f"处理新消息请求时发生错误: {str(e)}"
            )

    async def _analyze_message(self, message: NewMessageRequest, context: Dict[str, Any]) -> (str, Dict[str, Any]):
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
        if any(keyword in content for keyword in ["不对", "错了", "修正", "correction"]):
            return "handle_correction", {
                "message_id": message.message_id,
                "content": message.content
            }
        
        # 检查是否是简单查询
        if any(keyword in content for keyword in ["?", "？", "查询", "查一下"]):
            return "simple_query", {
                "message_id": message.message_id,
                "content": message.content
            }
        
        # 默认策略：创建新任务
        return "create_task", {
            "message_id": message.message_id,
            "content": message.content,
            "sender_id": message.sender_id,
            "conversation_id": message.conversation_id
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
