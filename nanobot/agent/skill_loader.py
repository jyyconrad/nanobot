"""
技能加载器组件 - 负责根据任务类型智能加载技能

SkillLoader 根据任务类型自动匹配和加载相关技能，
支持显式技能指定和默认技能加载策略。
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel

# 配置日志
logger = logging.getLogger(__name__)


class SkillMapping(BaseModel):
    """技能映射配置"""

    task_type: str
    skills: List[str]


class SkillLoader:
    """
    技能加载器 - 根据任务类型智能加载技能

    加载策略：
    1. 显式技能优先：用户明确指定的技能
    2. 任务类型映射：根据任务类型自动匹配技能
    3. 默认技能：加载 always skills

    核心功能：
    - 从配置文件加载技能映射
    - 根据任务类型匹配技能
    - 支持技能优先级管理
    """

    def __init__(self):
        self.skill_mapping = self._load_skill_mapping()
        self.default_skills = self._get_default_skills()

    def _load_skill_mapping(self) -> Dict[str, List[str]]:
        """
        从配置文件加载技能映射

        加载 config/skill_mapping.yaml 文件
        """
        config_path = Path(__file__).parent.parent / "config" / "skill_mapping.yaml"

        try:
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    if config and isinstance(config, dict) and "task_types" in config:
                        return config["task_types"]
        except Exception as e:
            logger.warning("加载技能映射配置失败: %s", e)

        # 默认技能映射
        default_mapping = {
            "coding": ["coding", "debugging", "testing"],
            "debugging": ["debugging", "coding", "testing"],
            "security": ["security", "coding", "testing"],
            "testing": ["testing", "coding", "debugging"],
            "planning": ["planning", "writing"],
            "writing": ["writing", "research"],
            "research": ["research", "writing"],
            "translation": ["writing"],
            "analysis": ["research", "planning"],
        }

        logger.debug("使用默认技能映射")
        return default_mapping

    def _get_default_skills(self) -> List[str]:
        """
        获取默认技能列表（always skills）
        """
        return ["planning", "writing"]

    async def load_skills_for_task(
        self, task_type: str, explicit_skills: Optional[List[str]] = None
    ) -> List[str]:
        """
        根据任务类型加载技能

        Args:
            task_type: 任务类型
            explicit_skills: 用户明确指定的技能列表（可选）

        Returns:
            技能列表（去重后）
        """
        logger.debug(
            "加载任务类型 '%s' 的技能，显式技能: %s", task_type, explicit_skills
        )

        skills = []

        # 1. 显式技能优先
        if explicit_skills:
            logger.debug("添加显式技能: %s", explicit_skills)
            skills.extend(explicit_skills)

        # 2. 任务类型映射
        if task_type in self.skill_mapping:
            mapped_skills = self.skill_mapping[task_type]
            logger.debug("添加任务类型 '%s' 映射的技能: %s", task_type, mapped_skills)
            skills.extend(mapped_skills)
        else:
            logger.debug("任务类型 '%s' 未在技能映射中找到", task_type)

        # 3. 默认技能
        logger.debug("添加默认技能: %s", self.default_skills)
        skills.extend(self.default_skills)

        # 去重并返回
        unique_skills = list(dict.fromkeys(skills))
        logger.debug("最终技能列表: %s", unique_skills)

        return unique_skills

    def get_task_type_mapping(self) -> Dict[str, List[str]]:
        """
        获取任务类型到技能的映射关系

        Returns:
            任务类型到技能列表的映射
        """
        return self.skill_mapping.copy()

    async def validate_skills(self, skills: List[str]) -> List[str]:
        """
        验证技能是否有效

        Args:
            skills: 技能列表

        Returns:
            有效技能列表
        """
        logger.debug("验证技能列表: %s", skills)

        valid_skills = []

        # 简单的验证逻辑（实际项目中应从技能系统获取有效技能列表）
        all_available_skills = set()
        for skill_list in self.skill_mapping.values():
            all_available_skills.update(skill_list)
        all_available_skills.update(self.default_skills)

        for skill in skills:
            if skill.lower() in all_available_skills:
                valid_skills.append(skill.lower())
            else:
                logger.warning("技能 '%s' 无效，已忽略", skill)

        logger.debug("有效技能列表: %s", valid_skills)

        return valid_skills

    @staticmethod
    def load_skill(skill_name: str) -> Dict[str, Any]:
        """
        加载技能内容（从 skills 目录读取 SKILL.md 文件）

        Args:
            skill_name: 技能名称

        Returns:
            包含技能内容的字典
        """
        logger.debug("正在加载技能 '%s' 的内容", skill_name)

        skill_dir = Path(__file__).parent.parent.parent / "skills" / skill_name.lower()
        skill_file = skill_dir / "SKILL.md"

        if not skill_file.exists():
            logger.warning("技能 '%s' 文件未找到: %s", skill_name, skill_file)
            return {
                "name": skill_name,
                "content": f"技能 '{skill_name}' 未找到或无法加载",
            }

        try:
            with open(skill_file, "r", encoding="utf-8") as f:
                content = f.read()

            logger.debug("技能 '%s' 内容加载成功", skill_name)
            return {
                "name": skill_name,
                "content": content.strip(),
            }
        except Exception as e:
            logger.warning("加载技能 '%s' 时出错: %s", skill_name, e)
            return {
                "name": skill_name,
                "content": f"技能 '{skill_name}' 加载失败: {str(e)}",
            }

    async def load_skill_content(self, skill_name: str) -> Optional[str]:
        """
        加载技能内容

        Args:
            skill_name: 技能名称

        Returns:
            技能内容，或 None 如果无法加载
        """
        try:
            skill_data = self.load_skill(skill_name)
            # 检查是否是有效的技能内容
            if "技能" in skill_data.get("content", "") and (
                "未找到" in skill_data.get("content")
                or "加载失败" in skill_data.get("content")
            ):
                return None
            return skill_data.get("content")
        except Exception as e:
            logger.warning("加载技能 '%s' 内容时出错: %s", skill_name, e)
            return None
