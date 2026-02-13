"""
EnhancedMemoryStore 单元测试 - 测试增强记忆系统功能

测试 EnhancedMemoryStore 的核心功能：
- 记忆添加和检索
- 记忆搜索
- 任务关联记忆
- 记忆管理
- 边界条件和错误处理
"""

from unittest.mock import patch

import pytest

from nanobot.agent.memory.enhanced_memory import EnhancedMemoryStore


class TestEnhancedMemoryStore:
    """EnhancedMemoryStore 单元测试类"""

    @pytest.fixture
    def memory_store(self, tmp_path):
        """创建 EnhancedMemoryStore 实例"""
        test_dir = tmp_path / "test_memory"
        test_dir.mkdir()
        return EnhancedMemoryStore(storage_dir=str(test_dir))

    @pytest.mark.asyncio
    async def test_add_and_retrieve_memory(self, memory_store):
        """测试添加和检索记忆"""
        memory_id = await memory_store.add_memory(
            content="测试记忆内容", tags=["test"], task_id="test_task"
        )

        memory = await memory_store.get_memory(memory_id)
        assert memory is not None
        assert memory.content == "测试记忆内容"
        assert "test" in memory.tags
        assert memory.task_id == "test_task"

    @pytest.mark.asyncio
    async def test_search_memory(self, memory_store):
        """测试记忆搜索功能"""
        await memory_store.add_memory(
            content="Python 编码技能", tags=["coding", "python"], task_id="coding_task"
        )
        await memory_store.add_memory(
            content="JavaScript 编码技能",
            tags=["coding", "javascript"],
            task_id="coding_task",
        )

        results = await memory_store.search_memory(
            query="Python", tags=["coding"], task_id="coding_task"
        )

        assert len(results) == 1
        assert "Python" in results[0].content

    @pytest.mark.asyncio
    async def test_get_task_memories(self, memory_store):
        """测试获取任务相关记忆"""
        await memory_store.add_memory(
            content="任务开始", tags=["task"], task_id="test_task_1"
        )
        await memory_store.add_memory(
            content="任务进行中", tags=["task"], task_id="test_task_1"
        )
        await memory_store.add_memory(
            content="无关记忆", tags=["general"], task_id="other_task"
        )

        task_memories = await memory_store.get_task_memories("test_task_1")

        assert len(task_memories) == 2
        assert all(memory.task_id == "test_task_1" for memory in task_memories)

    @pytest.mark.asyncio
    async def test_update_memory(self, memory_store):
        """测试更新记忆"""
        memory_id = await memory_store.add_memory(
            content="原始内容", tags=["original"], task_id="test_task"
        )

        success = await memory_store.update_memory(
            memory_id, content="更新后的内容", tags=["updated"], importance=5
        )

        assert success

        memory = await memory_store.get_memory(memory_id)
        assert memory.content == "更新后的内容"
        assert memory.tags == ["updated"]
        assert memory.importance == 5

    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_store):
        """测试删除记忆"""
        memory_id = await memory_store.add_memory(
            content="要删除的记忆", tags=["delete"], task_id="test_task"
        )

        success = await memory_store.delete_memory(memory_id)
        assert success

        memory = await memory_store.get_memory(memory_id)
        assert memory is None

    @pytest.mark.asyncio
    async def test_search_with_empty_query(self, memory_store):
        """测试空查询搜索"""
        await memory_store.add_memory(
            content="记忆1", tags=["tag1"], task_id="test_task"
        )
        await memory_store.add_memory(
            content="记忆2", tags=["tag2"], task_id="test_task"
        )

        results = await memory_store.search_memory(query="")

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_with_multiple_tags(self, memory_store):
        """测试多标签搜索"""
        await memory_store.add_memory(
            content="记忆1", tags=["tag1", "tag2"], task_id="test_task"
        )
        await memory_store.add_memory(
            content="记忆2", tags=["tag2"], task_id="test_task"
        )

        results = await memory_store.search_memory(tags=["tag1"])
        assert len(results) == 1

        results = await memory_store.search_memory(tags=["tag2"])
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_memory_importance(self, memory_store):
        """测试记忆重要性"""
        await memory_store.add_memory(
            content="重要记忆", tags=["important"], task_id="test_task", importance=8
        )
        await memory_store.add_memory(
            content="普通记忆", tags=["general"], task_id="test_task", importance=3
        )

        results = await memory_store.search_memory()
        assert len(results) == 2
        assert results[0].importance == 8
        assert results[0].content == "重要记忆"

    @pytest.mark.asyncio
    async def test_clean_old_memories(self, memory_store):
        """测试清理旧记忆"""
        # 使用 patch 正确模拟时间
        import datetime

        # 设置当前时间为固定值
        current_time = datetime.datetime(2024, 1, 15)
        old_timestamp = current_time - datetime.timedelta(days=31)
        new_timestamp = current_time - datetime.timedelta(days=15)

        with patch("nanobot.agent.memory.enhanced_memory.datetime") as mock_datetime:
            # 添加旧记忆
            mock_datetime.now.return_value = old_timestamp
            await memory_store.add_memory(
                content="旧记忆", tags=["old"], task_id="test_task", importance=0
            )

            # 添加新记忆
            mock_datetime.now.return_value = new_timestamp
            await memory_store.add_memory(
                content="新记忆", tags=["new"], task_id="test_task", importance=5
            )

            # 执行清理操作
            mock_datetime.now.return_value = current_time
            deleted = await memory_store.clean_old_memories(days=30)
            assert deleted == 1

        # 验证旧记忆被删除，新记忆保留
        memories = await memory_store.search_memory()
        assert len(memories) == 1
        assert "新记忆" in memories[0].content

    @pytest.mark.asyncio
    async def test_clear_task_memories(self, memory_store):
        """测试清除任务相关记忆"""
        await memory_store.add_memory(
            content="任务记忆1", tags=["task"], task_id="test_task"
        )
        await memory_store.add_memory(
            content="任务记忆2", tags=["task"], task_id="test_task"
        )

        deleted = await memory_store.clear_task_memories("test_task")
        assert deleted == 2

        task_memories = await memory_store.get_task_memories("test_task")
        assert len(task_memories) == 0

    @pytest.mark.asyncio
    async def test_search_with_limit(self, memory_store):
        """测试搜索结果限制"""
        for i in range(10):
            await memory_store.add_memory(
                content=f"记忆{i}", tags=["test"], task_id="test_task"
            )

        results = await memory_store.search_memory(limit=5)
        assert len(results) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
