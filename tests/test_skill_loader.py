"""
SkillLoader 单元测试 - 测试技能加载功能

测试 SkillLoader 的核心功能：
- 技能加载策略
- 任务类型映射
- 技能验证
- 配置加载
"""

import pytest

from nanobot.agent.skill_loader import SkillLoader


class TestSkillLoader:
    """SkillLoader 单元测试类"""

    @pytest.fixture
    def skill_loader(self):
        """创建 SkillLoader 实例"""
        return SkillLoader()

    @pytest.mark.asyncio
    async def test_load_skills_for_task(self, skill_loader):
        """测试加载任务类型相关技能"""
        skills = await skill_loader.load_skills_for_task("coding")

        assert len(skills) > 0
        assert "coding" in skills
        assert "debugging" in skills
        assert "testing" in skills

    @pytest.mark.asyncio
    async def test_load_skills_with_explicit_skills(self, skill_loader):
        """测试使用显式技能"""
        skills = await skill_loader.load_skills_for_task("coding", explicit_skills=["security"])

        assert "security" in skills
        assert "coding" in skills

    @pytest.mark.asyncio
    async def test_load_skills_for_unknown_task(self, skill_loader):
        """测试加载未知任务类型的技能"""
        skills = await skill_loader.load_skills_for_task("unknown_task")

        assert len(skills) > 0
        assert "planning" in skills
        assert "writing" in skills

    @pytest.mark.asyncio
    async def test_load_skills_default_only(self, skill_loader):
        """测试加载默认技能"""
        skills = await skill_loader.load_skills_for_task("unknown_task")

        assert "planning" in skills
        assert "writing" in skills

    @pytest.mark.asyncio
    async def test_validate_skills(self, skill_loader):
        """测试技能验证"""
        valid_skills = await skill_loader.validate_skills(["coding", "invalid_skill"])

        assert len(valid_skills) == 1
        assert "coding" in valid_skills

    @pytest.mark.asyncio
    async def test_validate_all_valid_skills(self, skill_loader):
        """测试验证所有有效技能"""
        valid_skills = await skill_loader.validate_skills(["coding", "writing"])

        assert len(valid_skills) == 2
        assert "coding" in valid_skills
        assert "writing" in valid_skills

    @pytest.mark.asyncio
    async def test_validate_no_skills(self, skill_loader):
        """测试验证空技能列表"""
        valid_skills = await skill_loader.validate_skills([])
        assert valid_skills == []

    @pytest.mark.asyncio
    async def test_validate_all_invalid_skills(self, skill_loader):
        """测试验证所有无效技能"""
        valid_skills = await skill_loader.validate_skills(["invalid1", "invalid2"])
        assert valid_skills == []

    @pytest.mark.asyncio
    async def test_load_skill_content(self, skill_loader):
        """测试加载技能内容"""
        content = await skill_loader.load_skill_content("coding")

        assert content is not None
        assert "编码技能" in content

    @pytest.mark.asyncio
    async def test_load_unknown_skill_content(self, skill_loader):
        """测试加载未知技能内容"""
        content = await skill_loader.load_skill_content("unknown_skill")

        assert content is None

    @pytest.mark.asyncio
    async def test_get_task_type_mapping(self, skill_loader):
        """测试获取任务类型映射"""
        mapping = skill_loader.get_task_type_mapping()

        assert isinstance(mapping, dict)
        assert len(mapping) > 0
        assert "coding" in mapping
        assert isinstance(mapping["coding"], list)

    @pytest.mark.asyncio
    async def test_skills_for_planning_task(self, skill_loader):
        """测试加载规划任务技能"""
        skills = await skill_loader.load_skills_for_task("planning")

        assert "planning" in skills
        assert "writing" in skills

    @pytest.mark.asyncio
    async def test_skills_for_security_task(self, skill_loader):
        """测试加载安全任务技能"""
        skills = await skill_loader.load_skills_for_task("security")

        assert "security" in skills
        assert "coding" in skills
        assert "testing" in skills

    @pytest.mark.asyncio
    async def test_skills_for_writing_task(self, skill_loader):
        """测试加载写作任务技能"""
        skills = await skill_loader.load_skills_for_task("writing")

        assert "writing" in skills
        assert "research" in skills


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
