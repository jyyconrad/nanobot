"""
测试提示词构建器功能

测试 PromptBuilder 类的主要功能，包括：
1. 基本初始化
2. 主智能体提示词构建
3. 子智能体提示词构建
4. 技能格式化
5. 决策指导提示词构建
"""

from pathlib import Path

import pytest

from nanobot.agent.prompt_builder import PromptBuilder, get_prompt_builder


class TestPromptBuilder:
    """测试提示词构建器"""

    def test_initialization(self):
        """测试提示词构建器初始化"""
        builder = PromptBuilder()
        assert isinstance(builder, PromptBuilder)

    def test_singleton_instance(self):
        """测试单例模式"""
        builder1 = get_prompt_builder()
        builder2 = get_prompt_builder()
        assert builder1 is builder2

    def test_build_main_agent_prompt(self):
        """测试主智能体提示词构建"""
        builder = PromptBuilder()
        prompt = builder.build_main_agent_prompt()
        assert isinstance(prompt, str)
        assert len(prompt.strip()) > 0
        assert "# MainAgent" in prompt or "# 你是 Nanobot MainAgent" in prompt

    def test_build_main_agent_prompt_with_custom_content(self):
        """测试带自定义内容的主智能体提示词构建"""
        builder = PromptBuilder()
        custom = "自定义提示词内容"
        append = "追加内容"
        prompt = builder.build_main_agent_prompt(
            custom_prompt=custom, append_system_prompt=append
        )
        assert custom in prompt
        assert append in prompt

    def test_build_subagent_prompt(self):
        """测试子智能体提示词构建"""
        builder = PromptBuilder()
        task = "测试任务"
        prompt = builder.build_subagent_prompt(task_description=task)
        assert isinstance(prompt, str)
        assert len(prompt.strip()) > 0
        assert task in prompt

    def test_build_agno_subagent_prompt(self):
        """测试 Agno 子智能体提示词构建"""
        builder = PromptBuilder()
        task = "测试任务"
        prompt = builder.build_subagent_prompt(task_description=task, agent_type="agno")
        assert isinstance(prompt, str)
        assert len(prompt.strip()) > 0
        assert task in prompt
        assert "Agno" in prompt

    def test_build_subagent_prompt_with_workspace(self):
        """测试带子工作区信息的子智能体提示词构建"""
        builder = PromptBuilder()
        task = "测试任务"
        workspace = "/test/workspace"
        prompt = builder.build_subagent_prompt(
            task_description=task, workspace=workspace
        )
        assert workspace in prompt

    def test_format_skills_for_prompt(self):
        """测试技能格式化"""
        builder = PromptBuilder()
        skills = ["coding", "writing"]
        formatted = builder.format_skills_for_prompt(skills)
        assert isinstance(formatted, str)
        assert len(formatted.strip()) > 0
        for skill in skills:
            assert skill in formatted

    def test_build_decision_guidance_prompt(self):
        """测试决策指导提示词构建"""
        builder = PromptBuilder()
        task = "测试任务"
        prompt = builder.build_decision_guidance_prompt(
            "task_analysis_prompt", task_description=task
        )
        assert isinstance(prompt, str)
        assert len(prompt.strip()) > 0
        assert task in prompt

    def test_build_skill_selection_prompt(self):
        """测试技能选择提示词构建"""
        builder = PromptBuilder()
        task = "测试任务"
        task_type = "coding"
        available_skills = ["coding", "writing", "debugging"]
        prompt = builder.build_decision_guidance_prompt(
            "skill_selection_prompt",
            task_description=task,
            task_type=task_type,
            available_skills=", ".join(available_skills),
        )
        assert isinstance(prompt, str)
        assert len(prompt.strip()) > 0
        assert task in prompt
        assert task_type in prompt
        for skill in available_skills:
            assert skill in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
