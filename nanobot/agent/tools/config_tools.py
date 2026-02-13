"""
配置查询工具 - 供 MainAgent 查询系统配置
"""

from pathlib import Path
from typing import Any, Dict, List

from nanobot.agent.tools.base import Tool


class GetAvailableSkillsTool(Tool):
    """获取可用的 skills 列表"""

    name = "get_available_skills"
    description = "获取系统中所有可用的技能列表及其描述"
    parameters = {}  # 无参数

    async def execute(self) -> str:
        """执行获取技能列表"""
        try:
            from nanobot.agent.skill_loader import SkillLoader

            loader = SkillLoader()
            mapping = loader.get_task_type_mapping()

            # 合并所有技能
            all_skills = set()
            for skill_list in mapping.values():
                all_skills.update(skill_list)

            # 添加默认技能
            default_skills = loader.default_skills
            all_skills.update(default_skills)

            # 格式化输出
            skills_info = []
            for skill in sorted(all_skills):
                skills_info.append(f"- {skill}")

            return "可用的技能列表：\n" + "\n".join(skills_info)

        except Exception as e:
            return f"获取技能列表失败: {str(e)}"


class GetSkillsForTaskTool(Tool):
    """根据任务类型获取推荐的 skills"""

    name = "get_skills_for_task"
    description = "根据任务类型获取推荐的技能列表"

    parameters = {
        "task_type": {
            "type": "string",
            "description": "任务类型 (如: coding, debugging, security, testing, planning, writing, research, translation, analysis)",
            "required": True,
        }
    }

    async def execute(self, task_type: str) -> str:
        """执行获取任务类型对应的技能"""
        try:
            from nanobot.agent.skill_loader import SkillLoader

            loader = SkillLoader()
            skills = await loader.load_skills_for_task(task_type)

            # 格式化输出
            skills_info = [f"任务类型: {task_type}"]
            skills_info.append("推荐的技能：")
            for skill in skills:
                skills_info.append(f"- {skill}")

            return "\n".join(skills_info)

        except Exception as e:
            return f"获取技能列表失败: {str(e)}"


class GetAvailableAgentsTool(Tool):
    """获取可用的 agent types"""

    name = "get_available_agents"
    description = "获取系统中支持的 agent 类型"
    parameters = {}  # 无参数

    async def execute(self) -> str:
        """执行获取 agent 类型"""
        try:
            # 系统支持的 agent 类型
            agent_types = {
                "agno": "Agno-based agent - 支持高级任务编排和人机交互",
                "default": "默认 agent - 基础任务执行能力",
            }

            agents_info = []
            for agent_type, description in agent_types.items():
                agents_info.append(f"- {agent_type}: {description}")

            return "可用的 agent 类型：\n" + "\n".join(agents_info)

        except Exception as e:
            return f"获取 agent 类型失败: {str(e)}"


class GetSkillContentTool(Tool):
    """获取技能的详细内容"""

    name = "get_skill_content"
    description = "获取指定技能的详细描述和使用说明"

    parameters = {
        "skill_name": {
            "type": "string",
            "description": "技能名称",
            "required": True,
        }
    }

    async def execute(self, skill_name: str) -> str:
        """执行获取技能内容"""
        try:
            from nanobot.agent.skill_loader import SkillLoader

            loader = SkillLoader()
            content = await loader.load_skill_content(skill_name)

            if content:
                return f"技能 '{skill_name}' 的详细内容：\n{content}"
            else:
                return f"未找到技能 '{skill_name}' 的内容"

        except Exception as e:
            return f"获取技能内容失败: {str(e)}"
