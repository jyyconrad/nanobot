"""
增强记忆系统 - 提供标签化和搜索功能的记忆存储

EnhancedMemoryStore 是增强的记忆系统，支持：
- 记忆的标签化存储
- 高级搜索功能（内容、标签、时间范围、任务关联）
- 任务关联记忆管理
- 重要性分级
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pathlib import Path
import json

from nanobot.agent.memory.models import Memory, MemorySearchQuery, MemorySearchResult

# 配置日志
logger = logging.getLogger(__name__)


class EnhancedMemoryStore:
    """
    增强记忆系统 - 提供标签化和搜索功能的记忆存储

    核心功能：
    - 添加记忆（支持标签和任务关联）
    - 搜索记忆（内容、标签、时间范围、任务关联）
    - 获取任务相关记忆
    - 记忆管理（更新、删除）
    """

    def __init__(self, storage_dir: str = "data/memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._memories: List[Memory] = []
        self._load_memories()

    def _load_memories(self):
        """从文件加载记忆"""
        try:
            memory_file = self.storage_dir / "memories.json"
            if memory_file.exists():
                with open(memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._memories = [Memory(**item) for item in data]
                logger.debug("从文件加载了 %d 条记忆", len(self._memories))
            else:
                logger.debug("记忆文件不存在，已创建新的记忆存储")
        except Exception as e:
            logger.warning("加载记忆失败: %s", e)
            self._memories = []

    def _save_memories(self):
        """保存记忆到文件"""
        try:
            memory_file = self.storage_dir / "memories.json"
            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump([memory.dict() for memory in self._memories], f, ensure_ascii=False, indent=2)
            logger.debug("成功保存了 %d 条记忆到文件", len(self._memories))
        except Exception as e:
            logger.warning("保存记忆失败: %s", e)

    async def add_memory(
        self,
        content: str,
        tags: List[str] = None,
        task_id: str = None,
        importance: int = 0
    ) -> str:
        """
        添加新记忆

        Args:
            content: 记忆内容
            tags: 记忆标签（可选）
            task_id: 关联的任务 ID（可选）
            importance: 重要性等级（0-10，默认 0）

        Returns:
            记忆的唯一标识符
        """
        logger.debug(
            "添加新记忆，内容长度: %d, 标签: %s, 任务 ID: %s",
            len(content),
            tags,
            task_id
        )

        memory = Memory(
            id=str(uuid.uuid4()),
            content=content,
            tags=tags or [],
            task_id=task_id,
            timestamp=datetime.now(),
            importance=importance
        )

        self._memories.append(memory)
        self._save_memories()

        logger.debug("记忆添加成功，ID: %s", memory.id)
        return memory.id

    async def search_memory(
        self,
        query: str = "",
        tags: List[str] = None,
        task_id: str = None,
        limit: int = 50
    ) -> List[Memory]:
        """
        搜索记忆

        Args:
            query: 内容搜索关键词（可选）
            tags: 标签过滤（可选）
            task_id: 任务 ID 过滤（可选）
            limit: 结果数量限制（默认 50）

        Returns:
            匹配的记忆列表
        """
        logger.debug(
            "搜索记忆，查询: '%s', 标签: %s, 任务 ID: %s, 限制: %d",
            query,
            tags,
            task_id,
            limit
        )

        start_time = datetime.now()
        results = []

        for memory in self._memories:
            # 内容匹配
            if query and query.lower() not in memory.content.lower():
                continue

            # 标签匹配
            if tags:
                memory_tags = set(tag.lower() for tag in memory.tags)
                search_tags = set(tag.lower() for tag in tags)
                if not search_tags.intersection(memory_tags):
                    continue

            # 任务 ID 匹配
            if task_id and memory.task_id != task_id:
                continue

            results.append(memory)

        # 按重要性和时间排序（重要性高的在前，时间近的在前）
        results.sort(
            key=lambda x: (-x.importance, -x.timestamp.timestamp())
        )

        # 限制结果数量
        limited_results = results[:limit]

        search_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        logger.debug(
            "搜索完成，找到 %d 条匹配的记忆，耗时: %.2fms",
            len(limited_results),
            search_time_ms
        )

        return limited_results

    async def get_task_memories(self, task_id: str) -> List[Memory]:
        """
        获取任务相关的所有记忆

        Args:
            task_id: 任务 ID

        Returns:
            任务相关的记忆列表
        """
        logger.debug("获取任务 '%s' 相关的记忆", task_id)

        task_memories = [
            memory for memory in self._memories
            if memory.task_id == task_id
        ]

        task_memories.sort(key=lambda x: x.timestamp)

        logger.debug("任务 '%s' 相关记忆数量: %d", task_id, len(task_memories))

        return task_memories

    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        根据 ID 获取记忆

        Args:
            memory_id: 记忆 ID

        Returns:
            记忆对象，或 None 如果未找到
        """
        logger.debug("查找记忆 ID: %s", memory_id)

        for memory in self._memories:
            if memory.id == memory_id:
                logger.debug("找到记忆 ID: %s", memory_id)
                return memory

        logger.debug("未找到记忆 ID: %s", memory_id)
        return None

    async def update_memory(
        self,
        memory_id: str,
        content: str = None,
        tags: List[str] = None,
        importance: int = None
    ) -> bool:
        """
        更新记忆

        Args:
            memory_id: 记忆 ID
            content: 新内容（可选）
            tags: 新标签（可选）
            importance: 新重要性（可选）

        Returns:
            更新是否成功
        """
        logger.debug(
            "更新记忆 ID: %s，内容: %s, 标签: %s, 重要性: %s",
            memory_id,
            content,
            tags,
            importance
        )

        memory = await self.get_memory(memory_id)
        if not memory:
            logger.warning("未找到要更新的记忆 ID: %s", memory_id)
            return False

        if content:
            memory.content = content
        if tags is not None:
            memory.tags = tags
        if importance is not None:
            memory.importance = importance

        memory.timestamp = datetime.now()
        self._save_memories()

        logger.debug("记忆更新成功，ID: %s", memory_id)
        return True

    async def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆

        Args:
            memory_id: 记忆 ID

        Returns:
            删除是否成功
        """
        logger.debug("删除记忆 ID: %s", memory_id)

        memory = await self.get_memory(memory_id)
        if not memory:
            logger.warning("未找到要删除的记忆 ID: %s", memory_id)
            return False

        self._memories.remove(memory)
        self._save_memories()

        logger.debug("记忆删除成功，ID: %s", memory_id)
        return True

    async def clean_old_memories(
        self,
        days: int = 30,
        min_importance: int = 0
    ) -> int:
        """
        清理旧记忆

        Args:
            days: 保留天数（默认 30 天）
            min_importance: 保留的最低重要性（默认 0）

        Returns:
            删除的记忆数量
        """
        logger.debug("清理 %d 天前且重要性低于 %d 的记忆", days, min_importance)

        cutoff_date = datetime.now() - timedelta(days=days)
        delete_count = 0

        for memory in list(self._memories):
            if (memory.timestamp < cutoff_date and
                memory.importance < min_importance):
                self._memories.remove(memory)
                delete_count += 1

        if delete_count > 0:
            self._save_memories()

        logger.debug("清理完成，删除了 %d 条旧记忆", delete_count)
        return delete_count

    async def clear_task_memories(self, task_id: str) -> int:
        """
        清除任务相关的所有记忆

        Args:
            task_id: 任务 ID

        Returns:
            删除的记忆数量
        """
        logger.debug("清除任务 '%s' 相关的记忆", task_id)

        delete_count = 0
        for memory in list(self._memories):
            if memory.task_id == task_id:
                self._memories.remove(memory)
                delete_count += 1

        if delete_count > 0:
            self._save_memories()

        logger.debug("任务 '%s' 记忆清除完成，删除了 %d 条记忆", task_id, delete_count)
        return delete_count
