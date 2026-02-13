"""
技能决策处理器 - MainAgent 智能决策的核心

这个处理器负责：
1. 调用工具查询系统配置（skills、agents）
2. 分析任务需求
3. 智能选择合适的 skills
4. 决定创建什么类型的 subagent
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..loop import AgentLoop
    from ..tools.registry import ToolRegistry

from .models import DecisionRequest, DecisionResult

logger = logging.getLogger(__name__)


class SkillDecisionHandler:
    """
    技能决策处理器

    这是 MainAgent 智能决策的核心，通过工具调用获取系统配置，
    智能地选择 skills 并创建合适类型的 subagent。
    """

    def __init__(
        self,
        agent_loop: "AgentLoop",
        tool_registry: "ToolRegistry",
        skill_loader,
    ):
        """
        初始化技能决策处理器

        Args:
            agent_loop: Agent 循环实例
            tool_registry: 工具注册表
            skill_loader: 技能加载器实例
        """
        self.agent_loop = agent_loop
        self.tool_registry = tool_registry
        self.skill_loader = skill_loader

    async def handle_request(self, request: DecisionRequest) -> DecisionResult:
        """
        处理技能决策请求

        Args:
            request: 决策请求

        Returns:
            决策结果
        """
        logger.info(f"SkillDecisionHandler: 处理请求 {request.request_type}")

        try:
            message_data = request.data
            task_description = message_data.get("content", "")

            # 步骤 1: 获取可用的配置信息
            config_info = await self._get_system_config()

            # 步骤 2: 分析任务并选择 skills
            selected_skills = await self._select_skills_for_task(
                task_description, config_info
            )

            # 步骤 3: 选择 agent 类型
            agent_type = await self._select_agent_type(task_description, config_info)

            # 步骤 4: 构建 subagent 配置
            subagent_config = {
                "agent_type": agent_type,
                "skills": selected_skills,
                "task_description": task_description,
            }

            logger.info(
                f"SkillDecisionHandler: 决策结果 - agent_type={agent_type}, skills={selected_skills}"
            )

            # 返回决策结果：创建 subagent
            return DecisionResult(
                success=True,
                action="spawn_subagent",
                message=f"已选择 {len(selected_skills)} 个技能，准备创建 {agent_type} 类型的 subagent",
                data={
                    "subagent_task": task_description,
                    "subagent_config": subagent_config,
                },
            )

        except Exception as e:
            logger.error(f"SkillDecisionHandler: 处理失败 - {e}", exc_info=True)
            return DecisionResult(
                success=False,
                action="error",
                message=f"技能决策失败: {str(e)}",
            )

    async def _get_system_config(self) -> Dict[str, Any]:
        """
        获取系统配置信息

        Returns:
            包含可用 skills 和 agents 的配置信息
        """
        config_info = {
            "available_skills": [],
            "available_agents": [],
            "skill_mapping": {},
        }

        try:
            # 获取可用的 skills
            if self.tool_registry.has("get_available_skills"):
                result = await self.tool_registry.execute("get_available_skills", {})
                config_info["available_skills"] = self._parse_skills_list(result)
                logger.debug(
                    f"SkillDecisionHandler: 可用 skills: {config_info['available_skills']}"
                )

            # 获取可用的 agents
            if self.tool_registry.has("get_available_agents"):
                result = await self.tool_registry.execute("get_available_agents", {})
                config_info["available_agents"] = self._parse_agents_list(result)
                logger.debug(
                    f"SkillDecisionHandler: 可用 agents: {config_info['available_agents']}"
                )

            # 获取技能映射
            config_info["skill_mapping"] = self.skill_loader.get_task_type_mapping()

        except Exception as e:
            logger.warning(f"SkillDecisionHandler: 获取配置失败 - {e}")

        return config_info

    async def _select_skills_for_task(
        self, task_description: str, config_info: Dict[str, Any]
    ) -> List[str]:
        """
        为任务选择合适的 skills

        Args:
            task_description: 任务描述
            config_info: 系统配置信息

        Returns:
            选择的技能列表
        """
        # 分析任务类型
        task_type = await self._analyze_task_type(task_description)
        logger.info(f"SkillDecisionHandler: 任务类型分析为: {task_type}")

        # 使用 SkillLoader 加载技能
        skills = await self.skill_loader.load_skills_for_task(task_type)

        logger.info(
            f"SkillDecisionHandler: 为任务选择了 {len(skills)} 个技能: {skills}"
        )
        return skills

    async def _analyze_task_type(self, task_description: str) -> str:
        """
        分析任务类型

        Args:
            task_description: 任务描述

        Returns:
            任务类型
        """
        # 简化的任务类型识别逻辑
        task_lower = task_description.lower()

        # 关键词匹配
        task_keywords = {
            "coding": [
                "代码",
                "函数",
                "class",
                "python",
                "javascript",
                "typescript",
                "java",
                "golang",
                "编程",
                "开发",
                "实现",
            ],
            "debugging": ["bug", "错误", "调试", "修复", "debug", "错误信息"],
            "testing": ["测试", "test", "单元测试", "测试用例", "coverage"],
            "security": ["安全", "漏洞", "安全审计", "security", "vulnerability"],
            "planning": ["规划", "计划", "设计", "架构", "任务分解"],
            "writing": ["文档", "写作", "write", "document", "说明"],
            "research": ["研究", "调研", "分析", "research", "search"],
            "analysis": ["分析", "数据", "报告", "analysis", "data"],
        }

        # 匹配关键词
        matched_types = []
        for task_type, keywords in task_keywords.items():
            for keyword in keywords:
                if keyword in task_lower:
                    matched_types.append(task_type)
                    break

        # 返回第一个匹配的类型，或默认为 planning
        return matched_types[0] if matched_types else "planning"

    async def _select_agent_type(
        self, task_description: str, config_info: Dict[str, Any]
    ) -> str:
        """
        选择 agent 类型

        Args:
            task_description: 任务描述
            config_info: 系统配置信息

        Returns:
            agent 类型
        """
        # 检查可用的 agents
        available_agents = config_info.get("available_agents", [])

        # 优先选择 agno（如果可用）
        if "agno" in available_agents:
            return "agno"

        # 否则使用 default
        return "default"

    def _parse_skills_list(self, result: str) -> List[str]:
        """
        解析技能列表

        Args:
            result: 工具执行结果字符串

        Returns:
            技能名称列表
        """
        skills = []
        lines = result.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("- "):
                skill_name = line[2:].strip()
                if skill_name:
                    skills.append(skill_name)
        return skills

    def _parse_agents_list(self, result: str) -> List[str]:
        """
        解析 agent 类型列表

        Args:
            result: 工具执行结果字符串

        Returns:
            agent 类型列表
        """
        agents = []
        lines = result.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("- "):
                # 提取 agent 名称（冒号前）
                parts = line[2:].split(":")
                if parts:
                    agent_name = parts[0].strip()
                    if agent_name:
                        agents.append(agent_name)
        return agents
