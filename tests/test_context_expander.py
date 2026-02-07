"""
ContextExpander 单元测试 - 测试上下文扩展功能

测试 ContextExpander 的核心功能：
- 上下文扩展
- 技能加载
- 任务类型匹配
- 边界条件和错误处理
"""

import pytest

from nanobot.agent.context_expander import ContextExpander


class TestContextExpander:
    """ContextExpander 单元测试类"""

    @pytest.fixture
    def expander(self):
        """创建 ContextExpander 实例"""
        return ContextExpander()

    @pytest.mark.asyncio
    async def test_expand_with_task_type(self, expander):
        """测试根据任务类型扩展上下文"""
        base_context = "基础上下文"
        task_type = "coding"

        expanded = await expander.expand(base_context, task_type)

        assert len(expanded) > len(base_context)
        assert "技能上下文" in expanded
        assert "编码技能" in expanded

    @pytest.mark.asyncio
    async def test_expand_without_task_type(self, expander):
        """测试无任务类型的扩展（不应该扩展）"""
        base_context = "基础上下文"

        expanded = await expander.expand(base_context)

        assert expanded == base_context

    @pytest.mark.asyncio
    async def test_expand_unknown_task_type(self, expander):
        """测试未知任务类型的扩展"""
        base_context = "基础上下文"
        task_type = "unknown_task_type"

        expanded = await expander.expand(base_context, task_type)

        assert "未找到与任务类型" in expanded or "未指定任务类型" in expanded

    @pytest.mark.asyncio
    async def test_load_skills(self, expander):
        """测试加载技能内容"""
        skills = await expander.load_skills(["coding", "writing"])

        assert len(skills) == 2
        assert any("编码技能" in skill for skill in skills)
        assert any("写作技能" in skill for skill in skills)

    @pytest.mark.asyncio
    async def test_load_invalid_skills(self, expander):
        """测试加载无效技能"""
        skills = await expander.load_skills(["invalid_skill", "nonexistent"])

        assert len(skills) == 0

    @pytest.mark.asyncio
    async def test_expand_coding_task(self, expander):
        """测试编码任务的上下文扩展"""
        base_context = "基础上下文"

        expanded = await expander.expand(base_context, "coding")

        assert "编码技能" in expanded
        assert "代码审查" in expanded
        assert "调试" in expanded

    @pytest.mark.asyncio
    async def test_expand_writing_task(self, expander):
        """测试写作任务的上下文扩展"""
        base_context = "基础上下文"

        expanded = await expander.expand(base_context, "writing")

        assert "写作技能" in expanded
        assert "内容创作" in expanded
        assert "文档生成" in expanded

    @pytest.mark.asyncio
    async def test_expand_research_task(self, expander):
        """测试研究任务的上下文扩展"""
        base_context = "基础上下文"

        expanded = await expander.expand(base_context, "research")

        assert "研究技能" in expanded
        assert "信息收集" in expanded
        assert "数据分析" in expanded

    @pytest.mark.asyncio
    async def test_expand_security_task(self, expander):
        """测试安全任务的上下文扩展"""
        base_context = "基础上下文"

        expanded = await expander.expand(base_context, "security")

        assert "安全技能" in expanded
        assert "代码安全审查" in expanded
        assert "漏洞检测" in expanded

    @pytest.mark.asyncio
    async def test_expand_multiple_skills(self, expander):
        """测试扩展包含多个技能的上下文"""
        base_context = "基础上下文"

        expanded = await expander.expand(base_context, "planning")

        assert len(expanded) > len(base_context)
        assert "规划技能" in expanded
        assert "任务分解" in expanded
        assert "项目管理" in expanded

    @pytest.mark.asyncio
    async def test_expand_with_empty_base_context(self, expander):
        """测试空基础上下文的扩展"""
        expanded = await expander.expand("", "coding")

        assert len(expanded) > 0
        assert "技能上下文" in expanded

    @pytest.mark.asyncio
    async def test_expand_with_long_base_context(self, expander):
        """测试长基础上下文的扩展"""
        long_context = "基础内容 " * 100
        expanded = await expander.expand(long_context, "coding")

        assert len(expanded) > len(long_context)
        assert "技能上下文" in expanded
        assert "编码技能" in expanded


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
