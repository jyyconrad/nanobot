"""
修正检测器

负责识别用户输入中的修正指令，用于调整之前的任务。
"""

import asyncio
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from nanobot.agent.planner.models import Correction, CorrectionPattern


class CorrectionDetector(BaseModel):
    """修正检测器"""
    correction_patterns: List[CorrectionPattern] = Field(default_factory=lambda: [
        CorrectionPattern(
            type="change",
            patterns=["修改.*", "变更.*", "更改.*", "调整.*", "替换.*"],
            weight=1.0
        ),
        CorrectionPattern(
            type="add",
            patterns=["添加.*", "增加.*", "补充.*", "新增.*"],
            weight=0.9
        ),
        CorrectionPattern(
            type="remove",
            patterns=["删除.*", "移除.*", "去掉.*", "取消.*"],
            weight=0.85
        ),
        CorrectionPattern(
            type="fix",
            patterns=["修复.*", "修正.*", "改错.*"],
            weight=0.8
        ),
        CorrectionPattern(
            type="improve",
            patterns=["优化.*", "改进.*", "提升.*", "完善.*"],
            weight=0.75
        ),
        CorrectionPattern(
            type="clarify",
            patterns=["澄清.*", "说明.*", "解释.*", "明确.*"],
            weight=0.7
        )
    ])

    negation_patterns: List[str] = Field(default_factory=lambda: [
        "不是.*", "不要.*", "不必.*", "不需要.*", "不用.*"
    ])

    class Config:
        """配置类"""
        arbitrary_types_allowed = True

    async def detect_correction(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Optional[Correction]:
        """
        检测修正指令

        Args:
            user_input: 用户输入文本
            context: 上下文信息

        Returns:
            修正信息或 None
        """
        try:
            # 检查是否是否定句
            if await self._is_negation(user_input):
                return None

            # 检测修正类型
            correction = await self._detect_correction_type(user_input)
            if correction:
                return correction

            # 根据上下文判断是否可能是修正
            if context:
                correction = await self._detect_correction_from_context(user_input, context)
                if correction:
                    return correction

            return None

        except Exception as e:
            raise Exception(f"修正检测失败: {str(e)}")

    async def _is_negation(self, user_input: str) -> bool:
        """
        检查是否是否定句

        Args:
            user_input: 用户输入文本

        Returns:
            是否是否定句
        """
        for pattern in self.negation_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return True
        return False

    async def _detect_correction_type(self, user_input: str) -> Optional[Correction]:
        """
        检测修正类型

        Args:
            user_input: 用户输入文本

        Returns:
            修正信息或 None
        """
        scores: Dict[str, float] = {}

        # 遍历所有修正模式
        for pattern in self.correction_patterns:
            score = 0.0
            for regex in pattern.patterns:
                if re.search(regex, user_input, re.IGNORECASE):
                    score += pattern.weight

            if score > 0:
                scores[pattern.type] = score

        if not scores:
            return None

        # 找到最高得分的修正类型
        best_type = max(scores.items(), key=lambda x: x[1])[0]
        best_score = scores[best_type]

        # 计算置信度
        total_score = sum(scores.values())
        confidence = min(best_score / total_score, 1.0)

        # 提取修正内容
        content = await self._extract_correction_content(user_input, best_type)

        # 提取修正目标
        target = await self._extract_correction_target(user_input)

        return Correction(
            type=best_type,
            content=content,
            target=target,
            confidence=confidence
        )

    async def _extract_correction_content(self, user_input: str, correction_type: str) -> str:
        """
        提取修正内容

        Args:
            user_input: 用户输入文本
            correction_type: 修正类型

        Returns:
            修正内容
        """
        # 简化实现，实际应根据修正类型提取具体内容
        return user_input

    async def _extract_correction_target(self, user_input: str) -> Optional[str]:
        """
        提取修正目标

        Args:
            user_input: 用户输入文本

        Returns:
            修正目标或 None
        """
        # 查找可能的目标模式
        target_patterns = [
            r"对(.+?)进行",
            r"针对(.+?)的",
            r"关于(.+?)的",
            r"修改(.+?)$",
            r"变更(.+?)$"
        ]

        for pattern in target_patterns:
            match = re.search(pattern, user_input)
            if match:
                return match.group(1).strip()

        return None

    async def _detect_correction_from_context(self, user_input: str, context: Dict[str, Any]) -> Optional[Correction]:
        """
        从上下文检测修正

        Args:
            user_input: 用户输入文本
            context: 上下文信息

        Returns:
            修正信息或 None
        """
        # 如果上下文中有最近的任务，但用户输入没有明确的修正关键词
        # 可能是隐含的修正
        if "last_task" in context:
            last_task = context["last_task"]

            # 检查用户输入是否与上一个任务相关
            if await self._is_related_to_last_task(user_input, last_task):
                # 检查是否有明确的修正关键词
                if await self._contains_correction_pattern(user_input):
                    return await self._detect_correction_type(user_input)
                else:
                    return Correction(
                        type="adjust",
                        content=user_input,
                        target=last_task.get("description"),
                        confidence=0.7
                    )

        return None

    async def _contains_correction_pattern(self, user_input: str) -> bool:
        """
        检查是否包含修正模式

        Args:
            user_input: 用户输入文本

        Returns:
            是否包含修正模式
        """
        for pattern in self.correction_patterns:
            for regex in pattern.patterns:
                if re.search(regex, user_input, re.IGNORECASE):
                    return True
        return False

    async def _is_related_to_last_task(self, user_input: str, last_task: Dict[str, Any]) -> bool:
        """
        检查是否与上一个任务相关

        Args:
            user_input: 用户输入文本
            last_task: 上一个任务信息

        Returns:
            是否与上一个任务相关
        """
        # 简单的关键词匹配
        if "description" in last_task:
            description = last_task["description"].lower()
            input_text = user_input.lower()

            # 检查是否包含相同的关键词
            common_words = ["代码", "文件", "数据", "分析", "搜索", "任务"]
            for word in common_words:
                if word in description and word in input_text:
                    return True

        return False

    async def is_correction(self, user_input: str) -> bool:
        """
        判断是否是修正指令

        Args:
            user_input: 用户输入文本

        Returns:
            是否是修正指令
        """
        return await self.detect_correction(user_input) is not None

    async def get_correction_type(self, user_input: str) -> Optional[str]:
        """
        获取修正类型

        Args:
            user_input: 用户输入文本

        Returns:
            修正类型或 None
        """
        correction = await self.detect_correction(user_input)
        return correction.type if correction else None

    async def get_correction_target(self, user_input: str) -> Optional[str]:
        """
        获取修正目标

        Args:
            user_input: 用户输入文本

        Returns:
            修正目标或 None
        """
        correction = await self.detect_correction(user_input)
        return correction.target if correction else None
