"""
Prompt Builder for Nanobot - Dynamic prompt construction system
参考 OpenClaw 的提示词架构，提供模块化、可维护的提示词构建功能

主要特点：
1. 动态构建提示词 - 根据可用工具和配置生成系统提示词
2. 分层结构 - 工具描述、指导原则、文档路径、项目上下文、技能
3. 支持条件性内容包含
4. 支持自定义提示词和追加内容
5. 技能集成 - 条件性包含技能（基于工具可用性）
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from nanobot.agent.tools.registry import ToolRegistry
from nanobot.config.loader import load_config
from nanobot.utils.helpers import get_project_context


class PromptBuilder:
    """
    提示词构建器 - 负责动态构建系统提示词

    支持以下功能：
    - 工具描述管理
    - 指导原则生成（根据可用工具）
    - 技能格式化
    - 项目上下文注入
    - 自定义提示词支持
    """

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        初始化提示词构建器

        Args:
            config_path: 提示词配置文件路径，默认为 nanobot/config/agent_prompts.yaml
        """
        self.config = self._load_prompt_config(config_path)
        self.skills_cache: Dict[str, str] = {}

    def _load_prompt_config(self, config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        加载提示词配置

        Args:
            config_path: 配置文件路径

        Returns:
            解析后的配置字典
        """
        if config_path is None:
            # 默认从项目目录加载
            project_dir = Path(__file__).parent.parent
            config_path = project_dir / "config" / "agent_prompts.yaml"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"提示词配置文件未找到: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def build_main_agent_prompt(
        self,
        custom_prompt: Optional[str] = None,
        append_system_prompt: Optional[str] = None,
        skills: Optional[List[str]] = None,
    ) -> str:
        """
        构建 MainAgent 系统提示词

        Args:
            custom_prompt: 自定义提示词内容（覆盖默认）
            append_system_prompt: 追加到系统提示词的内容
            skills: 要包含的技能列表（可选）

        Returns:
            完整的系统提示词字符串
        """
        if custom_prompt:
            base_prompt = custom_prompt
        else:
            base_prompt = self.config.get("main_agent", {}).get("system_prompt", "")

        # 构建完整提示词
        prompt_parts = []
        prompt_parts.append(base_prompt)

        # 添加项目上下文（如果有）
        project_context = get_project_context()
        if project_context:
            prompt_parts.append("\n## 项目上下文")
            prompt_parts.append(project_context)

        # 添加技能内容（如果有）
        if skills:
            prompt_parts.append("\n## 加载的技能")
            prompt_parts.append(self.format_skills_for_prompt(skills))

        # 追加自定义内容
        if append_system_prompt:
            prompt_parts.append("\n" + append_system_prompt)

        return "\n".join(prompt_parts)

    def build_subagent_prompt(
        self,
        task_description: str,
        skills: Optional[List[str]] = None,
        workspace: Optional[Union[str, Path]] = None,
        agent_type: str = "default",
        custom_prompt: Optional[str] = None,
        append_system_prompt: Optional[str] = None,
        available_tools: Optional[ToolRegistry] = None,
    ) -> str:
        """
        构建 Subagent 系统提示词

        Args:
            task_description: 任务描述
            skills: 加载的技能列表
            workspace: 工作区路径
            agent_type: 代理类型（default, agno 等）
            custom_prompt: 自定义提示词内容（覆盖默认）
            append_system_prompt: 追加到系统提示词的内容
            available_tools: 可用工具注册表

        Returns:
            完整的系统提示词字符串
        """
        # 获取对应的提示词模板
        if custom_prompt:
            template = custom_prompt
        elif agent_type == "agno":
            template = self.config.get("agno_subagent", {}).get("system_prompt_template", "")
        else:
            template = self.config.get("sub_agent", {}).get("system_prompt_template", "")

        # 格式化模板变量
        prompt = template.replace("{task_description}", task_description)

        if skills:
            skills_content = self.format_skills_for_prompt(skills)
            skills_list = "\n".join(f"- {skill}" for skill in skills)
            prompt = prompt.replace("{skills_content}", skills_content)
            prompt = prompt.replace("{skills_list}", skills_list)

        if workspace:
            prompt = prompt.replace("{workspace}", str(Path(workspace).resolve()))

        # 构建完整提示词
        prompt_parts = [prompt]

        # 添加工具描述（如果有工具信息）
        if available_tools:
            prompt_parts.append("\n## 可用工具")
            prompt_parts.append(self._format_tool_descriptions(available_tools))
            prompt_parts.append("\n## 使用工具的指导原则")
            prompt_parts.append(self._generate_guidelines_from_tools(available_tools))

        # 添加项目上下文（如果有）
        project_context = get_project_context()
        if project_context:
            prompt_parts.append("\n## 项目上下文")
            prompt_parts.append(project_context)

        # 追加自定义内容
        if append_system_prompt:
            prompt_parts.append("\n" + append_system_prompt)

        # 添加时间和工作区信息（如果尚未包含）
        if "{workspace}" not in template and workspace:
            prompt_parts.append(f"\n## 工作区\n你的工作目录：{Path(workspace).resolve()}")

        return "\n".join(prompt_parts)

    def format_skills_for_prompt(self, skills: List[str]) -> str:
        """
        格式化技能内容，用于提示词

        Args:
            skills: 技能名称列表

        Returns:
            格式化后的技能内容字符串
        """
        from nanobot.agent.skill_loader import SkillLoader

        formatted = []

        for skill_name in skills:
            # 从缓存获取技能内容（避免重复加载）
            if skill_name in self.skills_cache:
                content = self.skills_cache[skill_name]
            else:
                try:
                    skill = SkillLoader.load_skill(skill_name)
                    content = skill.get("content", "")
                    self.skills_cache[skill_name] = content
                except Exception as e:
                    content = f"技能 '{skill_name}' 加载失败: {str(e)}"
                    self.skills_cache[skill_name] = content

            formatted.append(f"### {skill_name}")
            formatted.append(content)

        return "\n".join(formatted)

    def _format_tool_descriptions(self, tools: ToolRegistry) -> str:
        """
        格式化工具描述，用于提示词

        Args:
            tools: 工具注册表

        Returns:
            格式化后的工具描述字符串
        """
        descriptions = []

        for tool in tools.get_tools():
            desc = (
                f"- **{tool.name}** - {tool.description}\n"
                f"  调用方式: `{tool.name}(...)`\n"
                f"  参数: {self._format_tool_parameters(tool.parameters)}"
            )
            descriptions.append(desc)

        return "\n".join(descriptions)

    def _format_tool_parameters(self, params: Dict[str, Any]) -> str:
        """
        格式化工具参数

        Args:
            params: 参数字典

        Returns:
            格式化后的参数字符串
        """
        if not params:
            return "无参数"

        param_descriptions = []
        for name, info in params.items():
            param_desc = f"{name}"
            if "type" in info:
                param_desc += f" ({info['type']})"
            if "description" in info:
                param_desc += f": {info['description']}"
            if "required" in info and info["required"]:
                param_desc += " (必需)"
            param_descriptions.append(param_desc)

        return ", ".join(param_descriptions)

    def _generate_guidelines_from_tools(self, tools: ToolRegistry) -> str:
        """
        根据可用工具生成指导原则

        Args:
            tools: 工具注册表

        Returns:
            生成的指导原则字符串
        """
        guidelines = []

        tool_names = [tool.name for tool in tools.get_tools()]

        if "read_file" in tool_names or "write_file" in tool_names or "list_dir" in tool_names:
            guidelines.append(
                "1. **文件操作**：在进行文件读取或写入操作时，请确保指定正确的文件路径，最好使用相对路径。"
            )
            guidelines.append("2. **目录操作**：使用 list_dir 查看目录内容时，注意检查返回结果是否包含预期文件。")

        if "exec" in tool_names:
            guidelines.append(
                "3. **命令执行**：执行系统命令时要谨慎，避免执行危险操作（如删除文件、修改系统配置）。"
            )
            guidelines.append(
                "4. **工作区限制**：命令默认限制在工作区内执行，如需访问外部资源，请评估风险。"
            )

        if "web_search" in tool_names or "web_fetch" in tool_names:
            guidelines.append("5. **网络搜索**：使用 web_search 查找信息时，确保搜索关键词准确。")
            guidelines.append("6. **网页获取**：使用 web_fetch 时，注意检查是否成功获取到内容。")

        if not guidelines:
            guidelines.append("1. **工具使用**：请根据任务需要合理使用提供的工具。")

        return "\n".join(guidelines)

    def build_decision_guidance_prompt(self, prompt_type: str, **kwargs) -> str:
        """
        构建决策指导提示词

        Args:
            prompt_type: 提示词类型 (task_analysis_prompt, skill_selection_prompt, etc.)
            **kwargs: 模板变量替换

        Returns:
            格式化后的决策指导提示词
        """
        template = self.config.get("decision_guidance", {}).get(prompt_type, "")

        # 替换模板变量
        prompt = template
        for key, value in kwargs.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))

        return prompt

    def get_tool_descriptions(self) -> Dict[str, Any]:
        """
        获取工具描述（用于序列化）

        Returns:
            工具描述字典
        """
        return {
            "read_file": {"name": "read_file", "description": "读取文件内容"},
            "write_file": {"name": "write_file", "description": "写入文件内容"},
            "list_dir": {"name": "list_dir", "description": "列出目录内容"},
            "exec": {"name": "exec", "description": "执行系统命令"},
            "web_search": {"name": "web_search", "description": "进行网络搜索"},
            "web_fetch": {"name": "web_fetch", "description": "获取网页内容"},
        }

    def get_guidelines(self, available_tools: Optional[ToolRegistry] = None) -> List[str]:
        """
        获取指导原则列表（根据工具可用性动态生成）

        Args:
            available_tools: 可用工具注册表

        Returns:
            指导原则列表
        """
        if available_tools:
            tool_names = [tool.name for tool in available_tools.get_tools()]
        else:
            tool_names = list(self.get_tool_descriptions().keys())

        guidelines = []

        if "read_file" in tool_names or "write_file" in tool_names:
            guidelines.append(
                "在进行文件操作时，请确保指定正确的路径，并检查操作结果是否符合预期。"
            )

        if "exec" in tool_names:
            guidelines.append(
                "执行命令时要谨慎，避免执行可能对系统造成损害的操作。"
            )

        if "web_search" in tool_names:
            guidelines.append(
                "使用网络搜索获取信息时，请确保搜索结果的相关性和准确性。"
            )

        if "web_fetch" in tool_names:
            guidelines.append(
                "获取网页内容时，注意检查返回结果是否包含所需信息。"
            )

        return guidelines


# 全局提示词构建器实例
_prompt_builder_instance: Optional[PromptBuilder] = None


def get_prompt_builder() -> PromptBuilder:
    """
    获取全局提示词构建器实例（单例模式）

    Returns:
        提示词构建器实例
    """
    global _prompt_builder_instance

    if _prompt_builder_instance is None:
        _prompt_builder_instance = PromptBuilder()

    return _prompt_builder_instance
