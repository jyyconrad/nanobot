"""
任务规划器

负责分析用户输入，识别任务类型，评估复杂度，并制定执行计划。
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from nanobot.agent.planner.models import TaskType, TaskPriority, TaskPlan
from nanobot.agent.planner.complexity_analyzer import ComplexityAnalyzer
from nanobot.agent.planner.task_detector import TaskDetector
from nanobot.agent.planner.correction_detector import CorrectionDetector
from nanobot.agent.planner.cancellation_detector import CancellationDetector


class TaskPlanner(BaseModel):
    """任务规划器"""
    complexity_analyzer: ComplexityAnalyzer = Field(default_factory=ComplexityAnalyzer)
    task_detector: TaskDetector = Field(default_factory=TaskDetector)
    correction_detector: CorrectionDetector = Field(default_factory=CorrectionDetector)
    cancellation_detector: CancellationDetector = Field(default_factory=CancellationDetector)

    class Config:
        """配置类"""
        arbitrary_types_allowed = True

    async def plan_task(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Union[TaskPlan, Dict[str, str]]:
        """
        规划任务执行计划

        Args:
            user_input: 用户输入文本
            context: 上下文信息

        Returns:
            任务执行计划或修正/取消指令
        """
        try:
            # 检查是否是取消指令
            if await self.cancellation_detector.is_cancellation(user_input):
                return {
                    "action": "cancel",
                    "reason": await self.cancellation_detector.get_reason(user_input)
                }

            # 检查是否是修正指令
            correction = await self.correction_detector.detect_correction(user_input, context)
            if correction:
                return {
                    "action": "correct",
                    "correction": correction
                }

            # 检测任务类型
            task_type = await self.task_detector.detect_task_type(user_input)

            # 分析复杂度
            complexity = await self.complexity_analyzer.analyze_complexity(user_input, task_type)

            # 生成执行计划
            plan = await self._generate_plan(user_input, task_type, complexity, context)

            return plan

        except Exception as e:
            raise Exception(f"任务规划失败: {str(e)}")

    async def _generate_plan(self, user_input: str, task_type: TaskType, complexity: float, context: Optional[Dict[str, Any]] = None) -> TaskPlan:
        """
        生成任务执行计划

        Args:
            user_input: 用户输入文本
            task_type: 任务类型
            complexity: 任务复杂度
            context: 上下文信息

        Returns:
            任务执行计划
        """
        # 根据任务类型和复杂度生成执行步骤
        steps = await self._generate_steps(user_input, task_type, complexity, context)

        # 估算执行时间
        estimated_time = self._estimate_time(complexity, len(steps))

        # 确定优先级
        priority = self._determine_priority(complexity, task_type)

        # 确定是否需要用户批准
        requires_approval = self._requires_approval(complexity, task_type)

        return TaskPlan(
            task_type=task_type,
            priority=priority,
            complexity=complexity,
            steps=steps,
            estimated_time=estimated_time,
            requires_approval=requires_approval
        )

    async def _generate_steps(self, user_input: str, task_type: TaskType, complexity: float, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        生成任务执行步骤

        Args:
            user_input: 用户输入文本
            task_type: 任务类型
            complexity: 任务复杂度
            context: 上下文信息

        Returns:
            执行步骤列表
        """
        # 简化实现，实际应根据任务类型和复杂度生成详细步骤
        steps = []

        if task_type == TaskType.CODE_GENERATION:
            steps = [
                "分析代码需求",
                "设计代码结构",
                "编写代码实现",
                "测试代码功能",
                "优化代码性能"
            ]
        elif task_type == TaskType.TEXT_SUMMARIZATION:
            steps = [
                "分析文本内容",
                "提取关键信息",
                "生成摘要",
                "优化摘要质量"
            ]
        elif task_type == TaskType.DATA_ANALYSIS:
            steps = [
                "分析数据需求",
                "收集数据",
                "清理数据",
                "分析数据",
                "可视化结果"
            ]
        elif task_type == TaskType.WEB_SEARCH:
            steps = [
                "分析搜索需求",
                "执行搜索",
                "处理搜索结果",
                "总结结果"
            ]
        elif task_type == TaskType.FILE_OPERATION:
            steps = [
                "分析文件操作需求",
                "执行文件操作",
                "验证操作结果"
            ]
        elif task_type == TaskType.SYSTEM_COMMAND:
            steps = [
                "分析系统命令需求",
                "执行系统命令",
                "检查命令结果"
            ]
        else:
            steps = [
                "分析任务需求",
                "执行任务",
                "检查结果"
            ]

        # 根据复杂度调整步骤数量
        if complexity < 0.3:
            steps = steps[:2]
        elif complexity < 0.7:
            steps = steps[:4]

        return steps

    def _estimate_time(self, complexity: float, step_count: int) -> int:
        """
        估算执行时间

        Args:
            complexity: 任务复杂度
            step_count: 步骤数量

        Returns:
            估计执行时间（秒）
        """
        base_time = 30  # 基础时间（秒）
        complexity_factor = 1 + complexity * 3  # 复杂度系数（1-4）
        step_factor = 1 + step_count * 0.2  # 步骤系数（1-2）

        return int(base_time * complexity_factor * step_factor)

    def _determine_priority(self, complexity: float, task_type: TaskType) -> TaskPriority:
        """
        确定任务优先级

        Args:
            complexity: 任务复杂度
            task_type: 任务类型

        Returns:
            任务优先级
        """
        if task_type == TaskType.SYSTEM_COMMAND or complexity > 0.8:
            return TaskPriority.URGENT
        elif task_type in [TaskType.CODE_GENERATION, TaskType.DATA_ANALYSIS] or complexity > 0.6:
            return TaskPriority.HIGH
        elif complexity > 0.4:
            return TaskPriority.MEDIUM
        else:
            return TaskPriority.LOW

    def _requires_approval(self, complexity: float, task_type: TaskType) -> bool:
        """
        确定是否需要用户批准

        Args:
            complexity: 任务复杂度
            task_type: 任务类型

        Returns:
            是否需要用户批准
        """
        if task_type == TaskType.SYSTEM_COMMAND or complexity > 0.7:
            return True
        return False

    async def is_complex_task(self, user_input: str) -> bool:
        """
        判断任务是否复杂

        Args:
            user_input: 用户输入文本

        Returns:
            是否为复杂任务
        """
        task_type = await self.task_detector.detect_task_type(user_input)
        complexity = await self.complexity_analyzer.analyze_complexity(user_input, task_type)
        return complexity > 0.6

    async def get_task_type(self, user_input: str) -> TaskType:
        """
        获取任务类型

        Args:
            user_input: 用户输入文本

        Returns:
            任务类型
        """
        return await self.task_detector.detect_task_type(user_input)
