"""
取消检测器

负责识别用户输入中的取消指令，用于终止正在执行的任务。
"""

import re
from typing import List, Optional

from pydantic import BaseModel, Field

from nanobot.agent.planner.models import CancellationPattern


class CancellationDetector(BaseModel):
    """取消检测器"""

    cancellation_patterns: List[CancellationPattern] = Field(
        default_factory=lambda: [
            CancellationPattern(
                patterns=["取消.*任务", "停止.*任务", "终止.*任务", "取消.*操作", "停止.*操作"],
                weight=0.85,
            ),
            CancellationPattern(patterns=["取消.*", "停止.*", "终止.*", "放弃.*"], weight=0.8),
            CancellationPattern(
                patterns=["我.*不想.*", "不要.*", "不必.*", "不需要.*", "不用.*"], weight=0.65
            ),
            CancellationPattern(patterns=["出错.*", "失败.*", "有问题.*", "错误.*"], weight=0.6),
        ]
    )

    confirmation_patterns: List[str] = Field(
        default_factory=lambda: ["确定.*取消", "确认.*取消", "是否.*取消", "真的.*取消"]
    )

    class Config:
        """配置类"""

        arbitrary_types_allowed = True

    async def is_cancellation(self, user_input: str) -> bool:
        """
        判断是否是取消指令

        Args:
            user_input: 用户输入文本

        Returns:
            是否是取消指令
        """
        try:
            # 检查是否是取消确认
            if await self._is_confirmation(user_input):
                return True

            # 检查是否包含取消模式
            if await self._contains_cancellation_pattern(user_input):
                return True

            return False

        except Exception as e:
            raise Exception(f"取消检测失败: {str(e)}")

    async def _is_confirmation(self, user_input: str) -> bool:
        """
        检查是否是取消确认

        Args:
            user_input: 用户输入文本

        Returns:
            是否是取消确认
        """
        for pattern in self.confirmation_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return True
        return False

    async def _contains_cancellation_pattern(self, user_input: str) -> bool:
        """
        检查是否包含取消模式

        Args:
            user_input: 用户输入文本

        Returns:
            是否包含取消模式
        """
        for pattern in self.cancellation_patterns:
            for regex in pattern.patterns:
                if re.search(regex, user_input, re.IGNORECASE):
                    return True
        return False

    async def get_reason(self, user_input: str) -> Optional[str]:
        """
        获取取消原因

        Args:
            user_input: 用户输入文本

        Returns:
            取消原因或 None
        """
        try:
            # 提取明确的取消原因
            reason_patterns = [
                r"因为(.+?)取消",
                r"由于(.+?)取消",
                r"取消.*因为(.+?)(?:，|。|！|？|$)",
                r"取消.*由于(.+?)(?:，|。|！|？|$)",
            ]

            for pattern in reason_patterns:
                match = re.search(pattern, user_input)
                if match:
                    reason = match.group(1).strip()
                    # 去除尾随的标点符号
                    if reason and reason[-1] in ["，", "。", "！", "？"]:
                        reason = reason[:-1]
                    return reason

            # 检查是否包含程序错误、网络问题等原因
            specific_patterns = [
                r"程序.*出错",
                r"程序.*错误",
                r"网络.*问题",
                r"网络.*故障",
                r"超时.*",
            ]
            for pattern in specific_patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    match = re.search(pattern, user_input)
                    if match:
                        return match.group(0).strip()

            # 检查是否包含错误相关的原因
            error_patterns = [r"出错.*", r"失败.*", r"有问题.*", r"错误.*"]
            for pattern in error_patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    match = re.search(pattern, user_input)
                    if match:
                        return match.group(0).strip()

            # 如果没有明确原因，返回默认原因
            if await self.is_cancellation(user_input):
                return "用户主动取消"

            return None

        except Exception as e:
            raise Exception(f"取消原因提取失败: {str(e)}")

    async def is_confirmation(self, user_input: str) -> bool:
        """
        判断是否是取消确认

        Args:
            user_input: 用户输入文本

        Returns:
            是否是取消确认
        """
        return await self._is_confirmation(user_input)

    async def get_confidence(self, user_input: str) -> float:
        """
        获取取消指令的置信度

        Args:
            user_input: 用户输入文本

        Returns:
            置信度 (0-1)
        """
        try:
            # 检查确认模式
            if await self._is_confirmation(user_input):
                return 0.95

            # 检查取消模式，只返回最高权重的模式
            max_weight = 0.0
            for pattern in self.cancellation_patterns:
                for regex in pattern.patterns:
                    if re.search(regex, user_input, re.IGNORECASE):
                        if pattern.weight > max_weight:
                            max_weight = pattern.weight

            return max_weight

        except Exception as e:
            raise Exception(f"置信度计算失败: {str(e)}")

    async def needs_confirmation(self, user_input: str) -> bool:
        """
        判断是否需要确认取消

        Args:
            user_input: 用户输入文本

        Returns:
            是否需要确认取消
        """
        # 如果是明确的取消指令，不需要确认
        explicit_patterns = [
            r"取消.*任务",
            r"停止.*任务",
            r"终止.*任务",
            r"取消.*操作",
            r"停止.*操作",
            r"确认.*取消",
        ]

        for pattern in explicit_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return False

        # 对于模糊的取消指令，需要确认
        return await self.is_cancellation(user_input)

    async def get_cancellation_type(self, user_input: str) -> Optional[str]:
        """
        获取取消类型

        Args:
            user_input: 用户输入文本

        Returns:
            取消类型或 None
        """
        if await self.is_cancellation(user_input):
            if await self._is_confirmation(user_input):
                return "confirmation"
            else:
                return "explicit"
        return None

    async def extract_cancellation_target(self, user_input: str) -> Optional[str]:
        """
        提取取消目标

        Args:
            user_input: 用户输入文本

        Returns:
            取消目标或 None
        """
        try:
            # 查找可能的目标模式
            target_patterns = [
                r"取消(.+?)任务",
                r"停止(.+?)任务",
                r"终止(.+?)任务",
                r"取消(.+?)操作",
                r"停止(.+?)操作",
            ]

            for pattern in target_patterns:
                match = re.search(pattern, user_input)
                if match:
                    return match.group(1).strip()

            return None

        except Exception as e:
            raise Exception(f"取消目标提取失败: {str(e)}")
