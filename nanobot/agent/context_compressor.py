"""
上下文压缩组件 - 负责动态压缩长对话上下文

ContextCompressor 使用 LLM 进行智能压缩，保留关键信息（任务、决定、重要结果）
同时去除冗余内容，确保上下文在 LLM 窗口限制内。
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class ContextStats:
    """上下文统计信息"""
    original_length: int
    compressed_length: int
    compression_ratio: float


class ContextCompressor:
    """
    上下文压缩器 - 使用 LLM 智能压缩长对话上下文

    核心功能：
    - 识别并保留关键信息（任务、决定、重要结果）
    - 去除冗余内容
    - 维持上下文的连贯性
    """

    async def compress(
        self,
        content: str,
        max_tokens: int = 200
    ) -> Tuple[str, ContextStats]:
        """
        压缩上下文内容到指定大小

        Args:
            content: 要压缩的内容
            max_tokens: 最大令牌数限制

        Returns:
            压缩后的内容和统计信息
        """
        logger.debug("开始压缩上下文，原始长度: %d", len(content))

        # 简单的压缩实现（实际项目中应使用 LLM 进行智能压缩）
        if len(content) <= max_tokens * 4:  # 假设每个 token 平均 4 个字符
            stats = ContextStats(
                original_length=len(content),
                compressed_length=len(content),
                compression_ratio=1.0
            )
            return content, stats

        # 简单的截断（实际项目中应使用更智能的压缩算法）
        compressed = content[:max_tokens * 4]

        stats = ContextStats(
            original_length=len(content),
            compressed_length=len(compressed),
            compression_ratio=len(compressed) / len(content)
        )

        logger.debug(
            "上下文压缩完成，压缩后长度: %d, 压缩率: %.2f",
            stats.compressed_length,
            stats.compression_ratio
        )

        return compressed, stats

    async def summarize_messages(self, messages: List[Dict]) -> str:
        """
        总结消息列表

        Args:
            messages: 消息列表

        Returns:
            消息总结
        """
        logger.debug("开始总结消息，消息数量: %d", len(messages))

        # 简单的总结实现（实际项目中应使用 LLM）
        if not messages:
            return ""

        # 提取关键信息
        task_keywords = ["任务", "目标", "需求", "要做"]
        decision_keywords = ["决定", "选择", "方案", "计划"]
        result_keywords = ["完成", "结果", "成功", "失败"]

        summaries = []
        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "user")

            for keyword in task_keywords:
                if keyword in content:
                    summaries.append(f"用户要求: {content}")
                    break

            for keyword in decision_keywords:
                if keyword in content:
                    summaries.append(f"决定: {content}")
                    break

            for keyword in result_keywords:
                if keyword in content:
                    summaries.append(f"结果: {content}")
                    break

        if summaries:
            summary = "\n".join(summaries)
        else:
            # 如果没有找到关键信息，返回最后几条消息
            last_messages = messages[-3:] if len(messages) > 3 else messages
            summary = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in last_messages
            ])

        logger.debug("消息总结完成，总结长度: %d", len(summary))

        return summary

    async def compress_messages(
        self,
        messages: List[Dict],
        max_tokens: int = 50
    ) -> Tuple[List[Dict], ContextStats]:
        """
        压缩消息列表

        Args:
            messages: 消息列表
            max_tokens: 最大令牌数限制

        Returns:
            压缩后的消息列表和统计信息
        """
        logger.debug("开始压缩消息列表，消息数量: %d", len(messages))

        # 计算总长度
        total_length = sum(len(msg.get("content", "")) for msg in messages)

        if total_length <= max_tokens * 4:
            stats = ContextStats(
                original_length=total_length,
                compressed_length=total_length,
                compression_ratio=1.0
            )
            return messages, stats

        # 智能压缩：只保留系统消息和用户消息，对助手消息进行总结
        compressed_messages = []
        assistant_messages = []

        for msg in messages:
            if msg.get("role") == "system" or msg.get("role") == "user":
                compressed_messages.append(msg)
            elif msg.get("role") == "assistant":
                assistant_messages.append(msg)

        # 对助手消息进行总结
        if assistant_messages:
            summary = await self.summarize_messages(assistant_messages)
            compressed_messages.append({
                "role": "system",
                "content": f"助手消息摘要: {summary}"
            })

        # 再次检查长度
        compressed_length = sum(len(msg.get("content", "")) for msg in compressed_messages)

        stats = ContextStats(
            original_length=total_length,
            compressed_length=compressed_length,
            compression_ratio=compressed_length / total_length
        )

        logger.debug(
            "消息列表压缩完成，压缩后消息数量: %d, 压缩率: %.2f",
            len(compressed_messages),
            stats.compression_ratio
        )

        return compressed_messages, stats
