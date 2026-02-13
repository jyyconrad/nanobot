"""
上下文监控组件 - 负责监控和管理对话上下文的token数量

ContextMonitor 用于：
1. 统计上下文中的token数量
2. 检查是否超过阈值
3. 自动触发上下文压缩
4. 管理上下文消息的添加和删除

支持文本消息、多模态消息（图像等）的token计数
支持不同模型的token限制配置
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# 配置日志
logger = logging.getLogger(__name__)


class ModelType(Enum):
    """支持的模型类型枚举"""

    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"
    GLM_4 = "glm-4"
    DOUBAO = "doubao"


@dataclass
class TokenLimits:
    """模型的token限制配置"""

    context_window: int = 4096
    max_completion_tokens: int = 1024


@dataclass
class CompressionEvent:
    """压缩事件记录"""

    timestamp: float
    original_token_count: int
    compressed_token_count: int
    compression_ratio: float
    reason: str = "Threshold exceeded"
    model: str = "default"


@dataclass
class ContextMonitorConfig:
    """ContextMonitor 配置"""

    model: str = ModelType.GPT_3_5_TURBO.value
    threshold: float = 0.8  # 默认 80% 阈值
    max_tokens: Optional[int] = None  # 如果提供，会覆盖模型默认值
    enable_auto_compression: bool = True
    compression_strategy: str = "intelligent"  # "intelligent" 或 "truncation"
    log_compression_events: bool = True


class ContextMonitor:
    """
    上下文监控器 - 管理和监控对话上下文的token数量

    核心功能：
    - 统计消息列表的token数量
    - 检查是否超过阈值
    - 自动或手动触发上下文压缩
    - 管理上下文消息的添加和删除
    - 记录压缩事件
    """

    # 模型默认token限制
    MODEL_TOKEN_LIMITS: Dict[str, TokenLimits] = {
        ModelType.GPT_3_5_TURBO.value: TokenLimits(
            context_window=4096, max_completion_tokens=1024
        ),
        ModelType.GPT_4.value: TokenLimits(
            context_window=8192, max_completion_tokens=2048
        ),
        ModelType.GPT_4_TURBO.value: TokenLimits(
            context_window=128000, max_completion_tokens=4096
        ),
        ModelType.CLAUDE_3_OPUS.value: TokenLimits(
            context_window=200000, max_completion_tokens=4096
        ),
        ModelType.CLAUDE_3_SONNET.value: TokenLimits(
            context_window=200000, max_completion_tokens=4096
        ),
        ModelType.CLAUDE_3_HAIKU.value: TokenLimits(
            context_window=200000, max_completion_tokens=4096
        ),
        ModelType.GLM_4.value: TokenLimits(
            context_window=8192, max_completion_tokens=2048
        ),
        ModelType.DOUBAO.value: TokenLimits(
            context_window=8192, max_completion_tokens=2048
        ),
    }

    def __init__(self, config: Optional[ContextMonitorConfig] = None):
        """
        初始化 ContextMonitor

        Args:
            config: ContextMonitor 配置，可选
        """
        self.config = config or ContextMonitorConfig()
        self.messages: List[Dict[str, Any]] = []
        self.compression_events: List[CompressionEvent] = []
        self._token_counter = self._create_token_counter()

        logger.debug(
            "ContextMonitor 初始化完成"
            f" - 模型: {self.config.model}"
            f" - 阈值: {self.config.threshold:.0%}"
            f" - 上下文窗口: {self.max_context_tokens}"
        )

    @property
    def max_context_tokens(self) -> int:
        """获取最大上下文token数量"""
        if self.config.max_tokens is not None:
            return self.config.max_tokens

        return self.MODEL_TOKEN_LIMITS.get(
            self.config.model, self.MODEL_TOKEN_LIMITS[ModelType.GPT_3_5_TURBO.value]
        ).context_window

    @property
    def threshold_tokens(self) -> int:
        """获取阈值对应的token数量"""
        return int(self.max_context_tokens * self.config.threshold)

    def _create_token_counter(self):
        """创建token计数器"""
        try:
            # 尝试使用 tiktoken 进行精确计数
            import tiktoken

            encoding = tiktoken.encoding_for_model(self.config.model)
            return lambda text: len(encoding.encode(text))
        except (ImportError, KeyError):
            # 备用方案：估算 token 数量（每个 token 平均 4 个字符）
            logger.warning(
                f"无法加载 tiktoken 或不支持的模型 {self.config.model}，"
                "将使用字符数估算 token 数量"
            )
            return lambda text: len(text) // 4

    def token_count(self, messages: Optional[List[Dict[str, Any]]] = None) -> int:
        """
        统计消息列表的token数量

        Args:
            messages: 要统计的消息列表，未提供时使用内部消息列表

        Returns:
            token数量
        """
        messages_to_count = messages or self.messages
        total_tokens = 0

        for msg in messages_to_count:
            role = msg.get("role", "")
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls", [])

            # 统计角色名
            total_tokens += len(role.split())  # 简单估算角色名的token数

            # 统计内容
            if isinstance(content, str):
                total_tokens += self._token_counter(content)
            elif isinstance(content, list):
                # 处理多模态内容
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            total_tokens += self._token_counter(item.get("text", ""))
                        elif item.get("type") == "image_url":
                            # 图像内容的token估算
                            total_tokens += 100  # 每张图像估算为100个token
                        else:
                            logger.warning(f"未知的内容类型: {item.get('type')}")
            else:
                logger.warning(f"未知的内容格式: {type(content)}")

            # 统计工具调用
            for tool_call in tool_calls:
                function = tool_call.get("function", {})
                tool_name = function.get("name", "")
                arguments = function.get("arguments", "")

                total_tokens += len(tool_name.split())
                total_tokens += self._token_counter(arguments)

        return total_tokens

    def check_threshold(self, messages: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        检查消息列表是否超过阈值

        Args:
            messages: 要检查的消息列表，未提供时使用内部消息列表

        Returns:
            是否超过阈值
        """
        token_count = self.token_count(messages)
        is_over_threshold = token_count > self.threshold_tokens

        if is_over_threshold:
            logger.warning(
                f"上下文token数量超过阈值: {token_count}/{self.threshold_tokens}"
                f" ({(token_count / self.max_context_tokens):.1%} of {self.max_context_tokens})"
            )

        return is_over_threshold

    async def compress_context(
        self, messages: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        压缩上下文，使token数量不超过阈值

        Args:
            messages: 要压缩的消息列表，未提供时使用内部消息列表

        Returns:
            压缩后的消息列表
        """
        messages_to_compress = messages or self.messages.copy()
        original_token_count = self.token_count(messages_to_compress)

        logger.debug(
            f"开始压缩上下文"
            f" - 原始token数: {original_token_count}"
            f" - 目标阈值: {self.threshold_tokens}"
            f" - 策略: {self.config.compression_strategy}"
        )

        # 根据压缩策略选择方法
        if self.config.compression_strategy == "truncation":
            compressed = await self._truncate_context(messages_to_compress)
        else:
            compressed = await self._intelligent_compression(messages_to_compress)

        compressed_token_count = self.token_count(compressed)
        compression_ratio = compressed_token_count / original_token_count

        # 记录压缩事件
        event = CompressionEvent(
            timestamp=1,  # 实际项目中使用 time.time()
            original_token_count=original_token_count,
            compressed_token_count=compressed_token_count,
            compression_ratio=compression_ratio,
            reason="Threshold exceeded",
            model=self.config.model,
        )
        self.compression_events.append(event)

        if self.config.log_compression_events:
            logger.info(
                f"上下文压缩完成"
                f" - 原始: {original_token_count}"
                f" - 压缩后: {compressed_token_count}"
                f" - 压缩率: {compression_ratio:.1%}"
            )

        return compressed

    async def _truncate_context(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        截断策略：保留系统消息和最后几条用户/助手消息

        Args:
            messages: 要压缩的消息列表

        Returns:
            压缩后的消息列表
        """
        compressed = []
        system_messages = []
        other_messages = []

        for msg in messages:
            if msg.get("role") == "system":
                system_messages.append(msg)
            else:
                other_messages.append(msg)

        # 保留所有系统消息
        compressed.extend(system_messages)

        # 从后往前添加其他消息，直到达到阈值
        temp_messages = []
        for msg in reversed(other_messages):
            temp_messages.insert(0, msg)
            temp_total = self.token_count(compressed + temp_messages)

            if temp_total <= self.threshold_tokens:
                compressed.extend(temp_messages)
                break
            else:
                temp_messages.pop(0)

        # 如果没有保留足够的消息，返回至少几条
        if len(compressed) <= len(system_messages):
            compressed.extend(other_messages[-2:])  # 至少保留最后2条消息

        return compressed

    async def _intelligent_compression(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        智能压缩：使用 LLM 进行总结压缩（需要集成 ContextCompressor）

        Args:
            messages: 要压缩的消息列表

        Returns:
            压缩后的消息列表
        """
        try:
            from nanobot.agent.context_compressor import ContextCompressor

            compressor = ContextCompressor()
            # 转换为适合压缩器的格式
            content_to_compress = "\n".join(
                [
                    f"{msg.get('role')}: {str(msg.get('content'))}"
                    for msg in messages
                    if msg.get("role") != "system"
                ]
            )

            max_content_tokens = self.threshold_tokens - sum(
                self.token_count([msg])
                for msg in messages
                if msg.get("role") == "system"
            )

            # 使用 ContextCompressor 压缩
            compressed_content, stats = await compressor.compress(
                content_to_compress, max_tokens=max_content_tokens // 4  # 估算字符数
            )

            # 重新构建消息结构
            compressed = []
            system_messages = [msg for msg in messages if msg.get("role") == "system"]
            compressed.extend(system_messages)

            if compressed_content:
                compressed.append(
                    {
                        "role": "system",
                        "content": f"对话历史摘要：\n{compressed_content}",
                    }
                )

            return compressed

        except ImportError as e:
            logger.error(f"无法加载 ContextCompressor：{e}，将使用截断策略")
            return await self._truncate_context(messages)

    def add_message(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        添加消息到上下文

        Args:
            message: 要添加的消息

        Returns:
            添加后的消息列表（可能已压缩）
        """
        logger.debug(
            f"添加消息"
            f" - 角色: {message.get('role')}"
            f" - 内容长度: {len(str(message.get('content')))} 字符"
        )

        self.messages.append(message)

        # 自动压缩检查
        if self.config.enable_auto_compression and self.check_threshold():
            logger.debug("自动触发上下文压缩")
            return self._trigger_auto_compression()

        return self.messages.copy()

    def remove_message(self, index: int) -> List[Dict[str, Any]]:
        """
        从上下文移除消息

        Args:
            index: 要移除的消息索引

        Returns:
            移除后的消息列表
        """
        if 0 <= index < len(self.messages):
            removed_msg = self.messages.pop(index)
            logger.debug(
                f"移除消息" f" - 索引: {index}" f" - 角色: {removed_msg.get('role')}"
            )
        else:
            logger.warning(f"无效的消息索引: {index}")

        return self.messages.copy()

    def get_messages(self) -> List[Dict[str, Any]]:
        """
        获取当前消息列表副本

        Returns:
            消息列表副本
        """
        return self.messages.copy()

    def get_compression_events(self) -> List[CompressionEvent]:
        """
        获取压缩事件历史

        Returns:
            压缩事件列表
        """
        return self.compression_events.copy()

    def _trigger_auto_compression(self) -> List[Dict[str, Any]]:
        """
        触发自动压缩

        Returns:
            压缩后的消息列表
        """
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，使用 run_coroutine_threadsafe
                future = asyncio.run_coroutine_threadsafe(self.compress_context(), loop)
                self.messages = future.result(timeout=30)
            else:
                # 否则直接运行
                self.messages = loop.run_until_complete(self.compress_context())
        except Exception as e:
            logger.error(f"自动压缩失败：{e}")

        return self.messages.copy()

    def clear(self) -> None:
        """
        清空所有消息和压缩事件
        """
        self.messages.clear()
        self.compression_events.clear()
        logger.debug("ContextMonitor 已清空")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取监控统计信息

        Returns:
            统计信息字典
        """
        return {
            "total_messages": len(self.messages),
            "total_tokens": self.token_count(),
            "max_context_tokens": self.max_context_tokens,
            "threshold_tokens": self.threshold_tokens,
            "compression_events": len(self.compression_events),
            "is_over_threshold": self.check_threshold(),
            "model": self.config.model,
            "threshold_ratio": self.config.threshold,
        }
