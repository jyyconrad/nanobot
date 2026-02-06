"""
ContextManager 单元测试 - 测试上下文管理增强组件

测试 ContextManager 的核心功能：
- 上下文构建
- 上下文压缩
- 上下文扩展
- 技能加载
- 边界条件和错误处理
"""


import pytest

from nanobot.agent.context_manager import ContextManager


class TestContextManager:
    """ContextManager 单元测试类"""

    @pytest.fixture
    def context_manager(self):
        """创建 ContextManager 实例"""
        return ContextManager()

    @pytest.mark.asyncio
    async def test_build_context_basic(self, context_manager):
        """测试基本上下文构建功能"""
        session_id = "test_session_1"
        context, stats = await context_manager.build_context(session_id)

        # 验证上下文包含基础内容
        assert "基础上下文" in context
        assert "记忆上下文" in context
        assert "技能上下文" in context

        # 验证统计信息
        assert stats.original_length > 0
        assert stats.compressed_length > 0
        assert stats.compression_ratio > 0

    @pytest.mark.asyncio
    async def test_build_context_with_task_type(self, context_manager):
        """测试根据任务类型构建上下文"""
        session_id = "test_session_2"
        task_type = "coding"
        context, stats = await context_manager.build_context(session_id, task_type)

        # 验证上下文包含任务相关的技能
        assert "技能上下文" in context
        assert any(keyword in context.lower() for keyword in ["coding", "debugging", "testing"])

    @pytest.mark.asyncio
    async def test_compress_context(self, context_manager):
        """测试上下文压缩功能"""
        # 创建一个很长的测试内容
        long_content = "测试 " * 1000
        messages = [{"role": "user", "content": long_content}]

        compressed, stats = await context_manager.compress_context(messages)

        # 验证压缩有效
        assert len(compressed) < len(long_content)
        assert stats.compression_ratio < 1.0
        assert stats.original_length > stats.compressed_length

    @pytest.mark.asyncio
    async def test_expand_context(self, context_manager):
        """测试上下文扩展功能"""
        base_context = "基础上下文"
        task_type = "coding"

        expanded = await context_manager.expand_context(base_context, task_type)

        # 验证上下文被扩展
        assert len(expanded) > len(base_context)
        assert "技能上下文" in expanded

    @pytest.mark.asyncio
    async def test_build_context_with_memory(self, context_manager):
        """测试包含记忆的上下文构建"""
        session_id = "test_session_3"

        # 首先添加一些记忆
        memory_id = await context_manager.memory_store.add_memory(
            content="这是一个测试记忆",
            tags=["session", session_id],
            task_id="test_task_1"
        )

        # 构建上下文
        context, stats = await context_manager.build_context(session_id)

        # 验证记忆被包含
        assert "测试记忆" in context

    @pytest.mark.asyncio
    async def test_build_context_with_unknown_task_type(self, context_manager):
        """测试未知任务类型的处理"""
        session_id = "test_session_4"
        task_type = "unknown_task_type"

        context, stats = await context_manager.build_context(session_id, task_type)

        # 验证技能上下文包含默认技能
        assert "未指定任务类型" in context or "未找到与任务类型" in context

    @pytest.mark.asyncio
    async def test_context_compression_accuracy(self, context_manager):
        """测试压缩后保留关键信息"""
        messages = [
            {"role": "user", "content": "我需要你帮我修复一个代码错误"},
            {"role": "assistant", "content": "我会帮你分析和修复代码错误"},
            {"role": "user", "content": "代码位于 nanobot/agent/context.py 文件中"},
            {"role": "assistant", "content": "我来检查这个文件"},
            {"role": "user", "content": "错误是在处理长上下文时发生的"},
            {"role": "assistant", "content": "我找到了问题所在，需要优化压缩算法"}
        ]

        compressed, stats = await context_manager.compress_context(messages)

        # 验证关键信息被保留
        assert any(keyword in compressed for keyword in ["代码错误", "压缩算法", "优化"])

    @pytest.mark.asyncio
    async def test_memory_search(self, context_manager):
        """测试记忆搜索功能"""
        session_id = "test_session_5"
        task_id = "test_task_2"

        # 先清理记忆存储，防止前序测试影响
        for memory in context_manager.memory_store._memories:
            if memory.task_id == task_id:
                context_manager.memory_store._memories.remove(memory)

        # 添加测试记忆
        await context_manager.memory_store.add_memory(
            content="测试代码优化",
            tags=["coding", "test"],
            task_id=task_id
        )
        await context_manager.memory_store.add_memory(
            content="测试文档写作",
            tags=["writing", "test"],
            task_id=task_id
        )

        # 搜索记忆
        memories = await context_manager.memory_store.search_memory(
            query="测试",
            tags=["coding"],
            task_id=task_id
        )

        # 验证搜索结果
        assert len(memories) == 1
        assert "代码优化" in memories[0].content

    @pytest.mark.asyncio
    async def test_skill_loading(self, context_manager):
        """测试技能加载功能"""
        skills = await context_manager.skill_loader.load_skills_for_task("coding")

        # 验证技能加载正确
        assert "coding" in skills
        assert "debugging" in skills
        assert "testing" in skills

    @pytest.mark.asyncio
    async def test_skill_validation(self, context_manager):
        """测试技能验证功能"""
        skills = await context_manager.skill_loader.validate_skills(["coding", "invalid_skill"])

        # 验证无效技能被过滤
        assert len(skills) == 1
        assert "coding" in skills


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
