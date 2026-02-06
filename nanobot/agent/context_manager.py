"""
上下文管理增强组件 - 负责构建、压缩和扩展上下文

ContextManager 是核心上下文管理类，提供智能的上下文处理功能，
包括上下文压缩、扩展和技能加载机制。
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

from pydantic import BaseModel

from nanobot.agent.context_compressor import ContextCompressor
from nanobot.agent.context_expander import ContextExpander
from nanobot.agent.skill_loader import SkillLoader
from nanobot.agent.memory.enhanced_memory import EnhancedMemoryStore

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class ContextStats:
    """上下文统计信息"""
    original_length: int
    compressed_length: int
    compression_ratio: float


class ContextManager:
    """
    上下文管理器 - 负责上下文的构建、压缩和扩展

    核心功能：
    - 动态压缩长对话上下文
    - 智能扩展上下文（加载任务相关技能）
    - 集成增强记忆系统
    """

    def __init__(self):
        self.compressor = ContextCompressor()
        self.expander = ContextExpander()
        self.skill_loader = SkillLoader()
        self.memory_store = EnhancedMemoryStore()

    async def build_context(
        self,
        session_id: str,
        task_type: Optional[str] = None,
        max_tokens: int = 4000
    ) -> Tuple[str, ContextStats]:
        """
        构建完整的上下文

        步骤：
        1. 加载基础上下文
        2. 加载记忆上下文
        3. 加载技能上下文（根据任务类型）
        4. 压缩上下文到指定大小

        Args:
            session_id: 会话 ID
            task_type: 任务类型
            max_tokens: 最大令牌数

        Returns:
            构建好的上下文字符串和统计信息
        """
        logger.debug("开始构建上下文，会话: %s, 任务类型: %s", session_id, task_type)

        # 1. 加载基础上下文（不变部分）
        base_context = self._load_base_context()

        # 2. 加载记忆上下文
        memory_context = await self._load_memory_context(session_id)

        # 3. 加载技能上下文
        skill_context = await self._load_skill_context(task_type)

        # 合并所有上下文
        full_context = "\n\n".join([
            base_context,
            memory_context,
            skill_context
        ])

        # 4. 压缩上下文到指定大小
        compressed_context, stats = await self.compressor.compress(
            full_context, max_tokens
        )

        logger.debug(
            "上下文构建完成，原始长度: %d, 压缩后长度: %d, 压缩率: %.2f",
            stats.original_length,
            stats.compressed_length,
            stats.compression_ratio
        )

        return compressed_context, stats

    async def compress_context(
        self,
        messages: List[Dict],
        max_tokens: int = 4000
    ) -> Tuple[str, ContextStats]:
        """
        压缩对话上下文

        Args:
            messages: 消息列表
            max_tokens: 最大令牌数

        Returns:
            压缩后的上下文和统计信息
        """
        return await self.compressor.compress(messages, max_tokens)

    async def expand_context(
        self,
        base_context: str,
        task_type: Optional[str] = None
    ) -> str:
        """
        智能扩展上下文（加载任务相关技能）

        Args:
            base_context: 基础上下文
            task_type: 任务类型

        Returns:
            扩展后的上下文
        """
        return await self.expander.expand(base_context, task_type)

    def _load_base_context(self) -> str:
        """
        加载基础上下文（不变部分）

        返回 AGENTS.md、TOOLS.md、IDENTITY.md 等基础信息
        """
        # TODO: 实际实现基础上下文加载
        return """# 基础上下文
- AGENTS.md: 定义了 Nanobot 的工作方式
- TOOLS.md: 记录了工具和技能信息
- IDENTITY.md: 定义了 Nanobot 的身份和定位
"""

    async def _load_memory_context(self, session_id: str) -> str:
        """
        加载记忆上下文

        从增强记忆系统中加载相关记忆
        """
        memories = await self.memory_store.search_memory(
            query="", tags=["session", session_id]
        )

        if not memories:
            return "## 记忆上下文\n暂无相关记忆"

        memory_texts = []
        for memory in memories:
            memory_texts.append(
                f"- [{memory.timestamp}] {memory.content}"
            )

        return "## 记忆上下文\n" + "\n".join(memory_texts)

    async def _load_skill_context(self, task_type: Optional[str]) -> str:
        """
        加载技能上下文

        根据任务类型加载相关技能信息
        """
        if not task_type:
            return "## 技能上下文\n未指定任务类型，使用默认技能"

        skills = await self.skill_loader.load_skills_for_task(task_type)

        if not skills:
            return f"## 技能上下文\n未找到与任务类型 '{task_type}' 相关的技能"

        skill_texts = []
        for skill in skills:
            skill_texts.append(f"- {skill}")

        return "## 技能上下文\n" + "\n".join(skill_texts)
