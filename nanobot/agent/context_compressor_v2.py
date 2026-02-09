"""
上下文压缩组件 - 负责动态压缩长对话上下文

ContextCompressor 使用 LLM 进行智能压缩，保留关键信息（任务、决定、重要结果）
同时去除冗余内容，确保上下文在 LLM 窗口限制内。

改进：
1. 使用更准确的 Token 计算（tiktoken）
2. 智能消息总结（保留最新内容，总结旧内容）
3. 支持上下文窗口限制
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logging.warning("tiktoken 未安装，将使用估算的 Token 计算")

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class ContextStats:
    """上下文统计信息"""

    original_length: int
    compressed_length: int
    compression_ratio: float
    original_tokens: int = 0
    compressed_tokens: int = 0
    messages_kept: int = 0
    messages_summarized: int = 0


class ContextCompressor:
    """
    上下文压缩器 - 使用智能算法压缩长对话上下文

    核心功能：
    - 识别并保留关键信息（任务、决定、重要结果）
    - 去除冗余内容
    - 维持上下文的连贯性
    - 保留最新消息，总结旧消息
    """

    def __init__(self, encoding: str = "cl100k_base"):
        """
        初始化压缩器

        Args:
            encoding: Token 编码名称，默认 cl100k_base (GPT-4)
        """
        self.encoding_name = encoding
        self.encoding = self._get_encoding(encoding)

    def _get_encoding(self, encoding: str):
        """获取 tiktoken 编码器"""
        if TIKTOKEN_AVAILABLE:
            try:
                return tiktoken.get_encoding(encoding)
            except Exception as e:
                logger.warning(f"无法加载编码 {encoding}: {e}")
                return None
        return None

    def count_tokens(self, text: str) -> int:
        """
        计算文本的 Token 数量

        Args:
            text: 要计算的文本

        Returns:
            Token 数量
        """
        if self.encoding:
            try:
                return len(self.encoding.encode(text))
            except Exception as e:
                logger.warning(f"Token 计算失败: {e}")

        # 降级：使用估算（1 token ≈ 1.6 字符）
        return int(len(text) / 1.6)

    async def compress(self, content: str, max_tokens: int = 4000) -> Tuple[str, ContextStats]:
        """
        压缩上下文内容到指定大小

        Args:
            content: 要压缩的内容
            max_tokens: 最大令牌数限制

        Returns:
            压缩后的内容和统计信息
        """
        logger.debug(
            "开始压缩上下文，原始长度:字符=%d, tokens≈%d",
            len(content),
            self.count_tokens(content),
        )

        original_tokens = self.count_tokens(content)

        # 如果不超过限制，直接返回
        if original_tokens <= max_tokens:
            stats = ContextStats(
                original_length=len(content),
                compressed_length=len(content),
                compression_ratio=1.0,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
            )
            return content, stats

        # 智能压缩：保留开头和结尾，中间用省略号
        # 开头保留 30%，结尾保留 70%（因为最新内容更重要）
        head_ratio = 0.3
        tail_ratio = 0.7

        head_tokens = int(max_tokens * head_ratio)
        tail_tokens = int(max_tokens * tail_ratio)

        # 分割内容
        head_content, tail_content = self._split_content(content, head_tokens, tail_tokens)

        # 构建压缩内容
        compressed = f"{head_content}\n\n... [中间内容已省略以节省上下文] ...\n\n{tail_content}"

        compressed_tokens = self.count_tokens(compressed)

        stats = ContextStats(
            original_length=len(content),
            compressed_length=len(compressed),
            compression_ratio=len(compressed) / len(content),
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
        )

        logger.debug(
            "上下文压缩完成，原始长度:字符=%d, tokens≈%d, 压缩后:字符=%d, tokens≈%d, 压缩率: %.2f",
            stats.original_length,
            stats.original_tokens,
            stats.compressed_length,
            stats.compressed_tokens,
            stats.compression_ratio,
        )

        return compressed, stats

    def _split_content(self, content: str, head_tokens: int, tail_tokens: int) -> Tuple[str, str]:
        """
        将内容分割为头部和尾部

        Args:
            content: 原始内容
            head_tokens: 头部 Token 数量
            tail_tokens: 尾部 Token 数量

        Returns:
            (头部, 尾部)
        """
        lines = content.split("\n")

        # 收集头部
        head_lines = []
        head_token_count = 0
        for line in lines:
            line_tokens = self.count_tokens(line) + 1  # +1 for newline
            if head_token_count + line_tokens > head_tokens:
                break
            head_lines.append(line)
            head_token_count += line_tokens

        # 收集尾部（从后往前）
        tail_lines = []
        tail_token_count = 0
        for line in reversed(lines):
            line_tokens = self.count_tokens(line) + 1  # +1 for newline
            if tail_token_count + line_tokens > tail_tokens:
                break
            tail_lines.append(line)
            tail_token_count += line_tokens

        # 尾部需要反转回来
        tail_lines.reverse()

        return "\n".join(head_lines), "\n".join(tail_lines)

    async def summarize_messages(self, messages: List[Dict]) -> str:
        """
        总结消息列表

        Args:
            messages: 消息列表

        Returns:
            消息总结
        """
        logger.debug("开始总结消息，消息数量: %d", len(messages))

        if not messages:
            return ""

        # 提取关键信息
        task_keywords = ["任务", "目标", "需求", "要做", "编写", "实现", "创建"]
        decision_keywords = ["决定", "选择", "方案", "计划", "分析", "评估"]
        result_keywords = ["完成", "结果", "成功", "失败", "错误"]

        summaries = []
        for msg in messages:
            content = msg.get.get("content", "")
            role = msg.get("role", "user")

            for keyword in task_keywords:
                if keyword in content:
                    summaries.append(f"用户要求: {content[:200]}")
                    break

            for keyword in decision_keywords:
                if keyword in content:
                    summaries.append(f"分析/决定: {content[:200]}")
                    break

            for keyword in result_keywords:
                if keyword in content:
                    summaries.append(f"执行结果: {content[:200]}")
                    break

        if summaries:
            summary = "\n".join(summaries[:10])  # 最多 10 条总结
        else:
            # 如果没有找到关键信息，返回最后 2 条消息
            last_messages = messages[-2:] if len(messages) > 2 else messages
            summary = "\n".join(
                [
                    f"{msg.get('role', 'user')}: {msg.get('content', '')[:200]}"
                    for msg in last_messages
                ]
            )

        logger.debug("消息总结完成，总结长度: %d", len(summary))

        return summary

    async def compress_messages(
        self, messages: List[Dict], max_tokens: int = 4000
    ) -> Tuple[List[Dict], ContextStats]:
        """
        压缩消息列表（智能保留最新内容）

        策略：
        1. 保留系统消息（永远保留）
        2. 保留最近的用户消息（最新 3 条）
        3. 对其他助手消息进行总结

        Args:
            messages: 消息列表
            max_tokens: 最大令牌数限制

        Returns:
            压缩后的消息列表和统计信息
        """
        logger.debug("开始压缩消息列表，消息数量: %d", len(messages))

        if not messages:
            return [], ContextStats(0, 0, 1.0, 0, 0, 0, 0)

        # 分离消息
        system_messages = []
        user_messages = []
        assistant_messages = []
        tool_messages = []

        for msg in messages:
            role = msg.get("role", "")
            if role == "system":
                system_messages.append(msg)
            elif role == "user":
                user_messages.append(msg)
            elif role == "assistant":
                assistant_messages.append(msg)
            elif role == "tool":
                tool_messages.append(msg)

        # 计算保留消息的 Token 数
        def count_msg_tokens(msg):
            return self.count_tokens(msg.get("content", "")) + 50  # overhead

        # 保留系统消息
        compressed_messages = system_messages.copy()
        used_tokens = sum(count_msg_tokens(msg) for msg in system_messages)

        # 保留最近的用户消息（最新 3 条）
        recent_user_messages = user_messages[-3:] if len(user_messages) > 3 else user_messages
        for msg in recent_user_messages:
            msg_tokens = count_msg_tokens(msg)
            if used_tokens + msg_tokens > max_tokens:
                break
            compressed_messages.append(msg)
            used_tokens += msg_tokens

        # 保留最近的工具调用（最新 5 条）
        recent_tool_messages = tool_messages[-5:] if len(tool_messages) > 5 else tool_messages
        for msg in recent_tool_messages:
            msg_tokens = count_msg_tokens(msg)
            if used_tokens + msg_tokens > max_tokens:
                break
            compressed_messages.append(msg)
            used_tokens += msg_tokens

        # 对助手消息进行总结（如果还有空间）
        if assistant_messages and used_tokens < max_tokens * 0.8:
            summary = await self.summarize_messages(assistant_messages)
            compressed_messages.append({"role": "system", "content": f"历史对话摘要:\n{summary}"})

        # 计算统计信息
        original_length = sum(len(msg.get("content", "")) for msg in messages)
        compressed_length = sum(len(msg.get("content", "")) for msg in compressed_messages)

        # 估算原始 Token 数
        original_tokens = sum(count_msg_tokens(msg) for msg in messages)

        stats = ContextStats(
            original_length=original_length,
            compressed_length=compressed_length,
            compression_ratio=compressed_length / original_length if original_length > 0 else 1.0,
            original_tokens=original_tokens,
            compressed_tokens=used_tokens,
            messages_kept=len(compressed_messages),
            messages_summarized=len(assistant_messages),
        )

        logger.debug(
            "消息列表压缩完成，原始消息数:%d, 压缩后:%d, Token:%d/%d, 压缩率: %.2f",
            len(messages),
            len(compressed_messages),
            stats.compressed_tokens,
            max_tokens,
            stats.compression_ratio,
        )

        return compressed_messages, stats
