"""
上下文管理增强组件 - 负责构建、压缩和扩展上下文

ContextManager 是核心上下文管理类，提供智能的上下文处理功能，
包括上下文压缩、扩展和技能加载机制。

改进：
1. 集成对话历史消息管理
2. 智能压缩策略（保留最新内容，总结旧内容）
3. 统一的 Token 计算
4. 支持上下文窗口限制
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import tiktoken

from nanobot.agent.context_compressor import ContextCompressor
from nanobot.agent.context_expander import ContextExpander
from nanobot.agent.memory.enhanced_memory import EnhancedMemoryStore
from nanobot.agent.skill_loader import SkillLoader

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
    messages_count: int = 0
    messages_kept: int = 0
    messages_summarized: int = 0


class ContextManagerV2:
    """
    上下文管理器（V2）- 负责上下文的构建、压缩和扩展

    核心功能：
    - 动态压缩长对话上下文（包括历史消息）
    - 智能扩展上下文（加载任务相关技能）
    - 集成增强记忆系统
    - 统一的 Token 管理
    """

    def __init__(
        self,
        max_system_tokens: int = 4000,
        max_history_tokens: int = 6000,
        encoding: str = "cl100k_base",
    ):
        self.max_system_tokens = max_system_tokens
        self.max_history_tokens = max_history_tokens
        self.compressor = ContextCompressor(encoding=encoding)
        self.expander = ContextExpander()
        self.skill_loader = SkillLoader()
        self.memory_store = EnhancedMemoryStore()
        self.history: List[Dict] = []  # 本地消息历史

        # Token 编码器
        self.encoding = encoding
        self.tokenizer = self._get_tokenizer(encoding)

    def _get_tokenizer(self, encoding: str):
        """获取 Token 编码器"""
        try:
            return tiktoken.get_encoding(encoding)
        except Exception as e:
            logger.warning(f"无法加载编码 {encoding}: {e}")
            return None

    def count_tokens(self, text: str) -> int:
        """计算文本的 Token 数量"""
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"Token 计算失败: {e}")
        # 降级：使用估算
        return int(len(text) / 1.6)

    def add_message(self, role: str, content: str, **kwargs):
        """
        添加消息到历史记录

        Args:
            role: 角色（user、assistant、system、tool）
            content: 消息内容
            **kwargs: 额外信息
        """
        msg = {"role": role, "content": content, **kwargs}
        self.history.append(msg)
        logger.debug(f"添加消息: role={role}, content 长度={len(content)}")

    def get_history(self, max_messages: int = 50) -> List[Dict]:
        """
        获取消息历史（支持限制数量）

        Args:
            max_messages: 最大消息数量

        Returns:
            消息历史列表
        """
        if len(self.history) > max_messages:
            return self.history[-max_messages:]
        return self.history.copy()

    async def build_context(
        self,
        session_id: str,
        task_type: Optional[str] = None,
        include_history: bool = True,
    ) -> Tuple[str, ContextStats]:
        """
        构建完整的上下文

        步骤：
        1. 加载基础上下文
        2. 加载记忆上下文
        3. 加载技能上下文（根据任务类型）
        4. 加载消息历史（如果启用）
        5. 压缩上下文到指定大小

        Args:
            session_id: 会话 ID
            task_type: 任务类型
            include_history: 是否包含消息历史

        Returns:
            构建好的上下文字符串和统计信息
        """
        logger.debug(
            "开始构建上下文，会话: %s, 任务类型: %s, 包含历史: %s",
            session_id,
            task_type,
            include_history,
        )

        parts = []
        original_length = 0

        # 1. 加载基础上下文（不变部分）
        base_context = self._load_base_context()
        parts.append(base_context)
        original_length += len(base_context)

        # 2. 加载记忆上下文
        memory_context = await self._load_memory_context(session_id)
        if memory_context:
            parts.append(memory_context)
            original_length += len(memory_context)

        # 3. 加载技能上下文
        skill_context = await self._load_skill_context(task_type)
        if skill_context:
            parts.append(skill_context)
            original_length += len(skill_context)

        # 合并系统上下文
        system_context = "\n\n".join(parts)

        # 压缩系统上下文
        compressed_system, system_stats = await self.compressor.compress(
            system_context, self.max_system_tokens
        )

        # 4. 加载和压缩消息历史
        if include_history and self.history:
            compressed_history, history_stats = await self.compressor.compress_messages(
                self.history, self.max_history_tokens
            )

            # 将历史转换为文本
            history_text = "\n\n".join(
                [
                    f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                    for msg in compressed_history
                ]
            )
        else:
            history_text = ""
            history_stats = ContextStats(0, 0, 1.0, 0, 0, 0, 0, 0)

        # 合并最终上下文
        if history_text:
            full_context = f"{compressed_system}\n\n## 对话历史\n\n{history_text}"
        else:
            full_context = compressed_system

        # 计算统计信息
        total_original_length = original_length + sum(
            len(msg.get("content", "")) for msg in self.history
        )
        compressed_length = len(full_context)

        stats = ContextStats(
            original_length=total_original_length,
            compressed_length=compressed_length,
            compression_ratio=(
                compressed_length / total_original_length
                if total_original_length > 0
                else 1.0
            ),
            original_tokens=system_stats.original_tokens
            + history_stats.original_tokens,
            compressed_tokens=system_stats.compressed_tokens
            + history_stats.compressed_tokens,
            messages_count=len(self.history),
            messages_kept=history_stats.messages_kept,
            messages_summarized=history_stats.messages_summarized,
        )

        logger.debug(
            "上下文构建完成，原始长度:字符=%d, tokens≈%d, 压缩后:字符=%d, tokens≈%d, 压缩率: %.2f, 消息: %d -> %d (总结: %d)",
            stats.original_length,
            stats.original_tokens,
            stats.compressed_length,
            stats.compressed_tokens,
            stats.compression_ratio,
            stats.messages_count,
            stats.messages_kept,
            stats.messages_summarized,
        )

        return full_context, stats

    async def compress_context(
        self, messages: List[Dict], max_tokens: int = 4000
    ) -> Tuple[List[Dict], ContextStats]:
        """
        压缩对话上下文

        Args:
            messages: 消息列表
            max_tokens: 最大令牌数

        Returns:
            压缩后的消息列表和统计信息
        """
        return await self.compressor.compress_messages(messages, max_tokens)

    async def expand_context(
        self, base_context: str, task_type: Optional[str] = None
    ) -> str:
        """
        智能扩展上下文（加载任务相关技能） Args:
            base_context: 基础上下文
            task_type: 任务类型

        Returns:
            扩展后的上下文
        """
        return await self.expander.expand(base_context, task_type)

    def _load_base_context(self) -> str:
        """
        加载基础上下文（不变部分）

        从以下位置按优先级加载：
        1. workspace/AGENTS.md - 用户自定义（最高优先级）
        2. workspace/TOOLS.md - 用户自定义
        3. workspace/IDENTITY.md - 用户自定义
        4. nanobot/config/agent_prompts.yaml - 默认配置

        Returns:
            基础上下文字符串
        """
        import yaml

        context_parts = []

        # 定义要加载的文件列表（按优先级）
        files_to_load = [
            ("AGENTS.md", "## 代理定义"),
            ("TOOLS.md", "## 工具定义"),
            ("IDENTITY.md", "## 身份定义"),
        ]

        # 1. 尝试从 workspace 加载用户自定义配置
        workspace_paths = [
            Path("workspace"),
            Path(__file__).parent.parent.parent / "workspace",
            Path.cwd() / "workspace",
        ]

        workspace = None
        for wp in workspace_paths:
            if wp.exists() and wp.is_dir():
                workspace = wp
                break

        if workspace:
            for filename, header in files_to_load:
                file_path = workspace / filename
                if file_path.exists():
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        if content.strip():
                            context_parts.append(f"{header}\n\n{content}")
                            logger.debug(f"已加载基础上下文文件: {file_path}")
                    except Exception as e:
                        logger.warning(f"加载基础上下文文件失败 {file_path}: {e}")

        # 2. 如果没有找到用户自定义配置，使用默认配置
        if not context_parts:
            default_config_path = (
                Path(__file__).parent.parent / "config" / "agent_prompts.yaml"
            )
            if default_config_path.exists():
                try:
                    with open(default_config_path, "r", encoding="utf-8") as f:
                        config = yaml.safe_load(f) or {}

                    # 提取默认配置内容
                    main_agent = config.get("main_agent", {})
                    if main_agent:
                        context_parts.append(f"## 主代理配置\n\n{main_agent}")

                    sub_agent = config.get("sub_agent", {})
                    if sub_agent:
                        context_parts.append(f"## 子代理配置\n\n{sub_agent}")

                    logger.debug(f"已加载默认基础上下文配置: {default_config_path}")

                except Exception as e:
                    logger.warning(f"加载默认基础上下文配置失败: {e}")

        # 3. 如果仍然没有内容，使用最小化默认内容
        if not context_parts:
            logger.warning("未能加载任何基础上下文配置，使用最小化默认内容")
            context_parts = [
                "## 基础上下文\n\nNanobot 是一个 AI 助手，帮助用户完成各种任务。"
            ]

        # 合并所有上下文部分
        full_context = "\n\n---\n\n".join(context_parts)

        logger.debug(f"基础上下文加载完成，总长度: {len(full_context)} 字符")

        return full_context

    async def _load_memory_context(self, session_id: str) -> str:
        """
        加载记忆上下文

        从增强记忆系统中加载相关记忆
        """
        memories = await self.memory_store.search_memory(
            query="", tags=["session", session_id], limit=10  # 限制记忆数量
        )

        if not memories:
            return ""

        memory_texts = []
        for memory in memories:
            memory_texts.append(f"- [{memory.timestamp}] {memory.content[:100]}")

        return "## 记忆上下文\n" + "\n".join(memory_texts[:10])  # 最多 10 条

    async def _load_skill_context(self, task_type: Optional[str]) -> str:
        """
        加载技能上下文

        根据任务类型加载相关技能信息
        """
        if not task_type:
            return "## 技能上下文\n未指定任务类型，使用默认技能"

        # 检查任务类型是否已知
        task_mapping = self.skill_loader.get_task_type_mapping()
        if task_type not in task_mapping:
            return f"## 技能上下文\n未找到与任务类型 '{task_type}' 相关的技能"

        skills = await self.skill_loader.load_skills_for_task(task_type)

        if not skills:
            return f"## 技能上下文\n未找到与任务类型 '{task_type}' 相关的技能"

        # 限制技能内容长度
        skill_texts = []
        for skill in skills:
            skill_texts.append(f"- {skill}")

        return "## 技能上下文\n" + "\n".join(skill_texts[:10])  # 最多 10 个技能

    def clear_history(self):
        """清除消息历史"""
        self.history.clear()
        logger.debug("消息历史已清除")

    def get_context_stats(self) -> Dict:
        """
        获取上下文统计信息

        Returns:
            统计信息字典
        """
        history_tokens = sum(
            self.count_tokens(msg.get("content", "")) for msg in self.history
        )

        return {
            "history_length": len(self.history),
            "history_tokens": history_tokens,
        }
