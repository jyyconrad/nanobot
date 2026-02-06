"""
上下文扩展组件 - 负责智能扩展上下文

ContextExpander 根据任务类型自动加载相关技能和配置，
动态调整上下文窗口大小以适应任务需求。
"""

import asyncio
import logging
from typing import List, Optional

from pydantic import BaseModel

from nanobot.agent.skill_loader import SkillLoader

# 配置日志
logger = logging.getLogger(__name__)


class ContextExpander:
    """
    上下文扩展器 - 根据任务类型智能扩展上下文

    核心功能：
    - 根据任务类型加载相关技能
    - 自动调整上下文窗口大小
    - 集成任务相关的配置信息
    """

    def __init__(self):
        self.skill_loader = SkillLoader()

    async def expand(
        self,
        base_context: str,
        task_type: Optional[str] = None
    ) -> str:
        """
        扩展上下文

        Args:
            base_context: 基础上下文
            task_type: 任务类型

        Returns:
            扩展后的上下文
        """
        logger.debug("开始扩展上下文，任务类型: %s", task_type)

        if not task_type:
            logger.debug("未指定任务类型，返回基础上下文")
            return base_context

        # 加载任务相关技能
        skills = await self.skill_loader.load_skills_for_task(task_type)
        logger.debug("为任务类型 '%s' 加载了 %d 个技能", task_type, len(skills))

        if not skills:
            logger.debug("未找到任务类型 '%s' 相关的技能", task_type)
            return base_context

        # 构建技能上下文
        skill_context = await self._build_skill_context(skills)

        # 合并到基础上下文
        expanded_context = "\n\n".join([
            base_context,
            skill_context
        ])

        logger.debug("上下文扩展完成，扩展后长度: %d", len(expanded_context))

        return expanded_context

    async def load_skills(self, skill_names: List[str]) -> List[str]:
        """
        加载技能内容

        Args:
            skill_names: 技能名称列表

        Returns:
            技能内容列表
        """
        logger.debug("开始加载技能，技能数量: %d", len(skill_names))

        # 简单的技能内容加载（实际项目中应从技能系统加载）
        skill_contents = []
        for skill_name in skill_names:
            skill_content = await self._load_skill_content(skill_name)
            if skill_content:
                skill_contents.append(skill_content)

        logger.debug("技能加载完成，成功加载 %d 个技能", len(skill_contents))

        return skill_contents

    async def _build_skill_context(self, skills: List[str]) -> str:
        """
        构建技能上下文

        Args:
            skills: 技能名称列表

        Returns:
            技能上下文字符串
        """
        logger.debug("开始构建技能上下文，技能数量: %d", len(skills))

        skill_contents = await self.load_skills(skills)

        if not skill_contents:
            return "## 技能上下文\n未找到可用的技能内容"

        context_parts = ["## 技能上下文"]
        for i, content in enumerate(skill_contents, 1):
            context_parts.append(f"### 技能 {i}: {content[:50]}...")
            context_parts.append(content)

        return "\n".join(context_parts)

    async def _load_skill_content(self, skill_name: str) -> Optional[str]:
        """
        加载单个技能内容

        Args:
            skill_name: 技能名称

        Returns:
            技能内容，或 None 如果无法加载
        """
        logger.debug("正在加载技能 '%s'", skill_name)

        # 简单的模拟实现（实际项目中应从技能系统加载）
        skill_templates = {
            "coding": """# 编码技能
- 支持多种编程语言
- 提供代码审查和重构功能
- 支持测试驱动开发
- 自动修复代码问题
""",
            "debugging": """# 调试技能
- 支持错误定位和分析
- 提供调试建议和修复方案
- 支持堆栈跟踪分析
- 自动识别常见错误模式
""",
            "security": """# 安全技能
- 代码安全审查
- 漏洞检测和修复
- 安全最佳实践建议
- 依赖库安全检查
""",
            "testing": """# 测试技能
- 单元测试生成
- 集成测试支持
- 测试覆盖分析
- 性能测试工具
""",
            "planning": """# 规划技能
- 任务分解和规划
- 项目管理支持
- 时间表和里程碑设置
- 风险评估和缓解
""",
            "writing": """# 写作技能
- 内容创作和编辑
- 文档生成和优化
- 语言风格检查
- 翻译支持
""",
            "research": """# 研究技能
- 信息收集和分析
- 数据挖掘支持
- 文献检索和整理
- 研究报告生成
"""
        }

        content = skill_templates.get(skill_name.lower())
        if content:
            logger.debug("技能 '%s' 加载成功", skill_name)
        else:
            logger.warning("技能 '%s' 未找到", skill_name)

        return content
