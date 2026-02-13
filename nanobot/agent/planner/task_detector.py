"""
任务检测器

负责识别用户输入中的任务类型。
"""

import re
from typing import Any, Dict, List

from pydantic import BaseModel, Field, ConfigDict

from nanobot.agent.planner.models import TaskDetectionResult, TaskPattern, TaskType


class TaskDetector(BaseModel):
    """任务检测器"""

    patterns: List[TaskPattern] = Field(
        default_factory=lambda: [
            TaskPattern(
                task_type=TaskType.CODE_GENERATION,
                patterns=[
                    "写.*代码",
                    "编写.*函数",
                    "编写.*程序",
                    "实现.*功能",
                    "实现.*程序",
                    "开发.*应用",
                    "修复.*bug",
                    "重构.*代码",
                    "优化.*性能",
                    "实现.*系统",
                    "开发.*系统",
                    "图像识别",
                    "数据预处理",
                    "特征提取",
                    "模型训练",
                    "机器学习",
                ],
                weight=1.0,
            ),
            TaskPattern(
                task_type=TaskType.TEXT_SUMMARIZATION,
                patterns=[
                    "总结.*",
                    "概括.*",
                    "摘要.*",
                    "简述.*",
                    "整理.*要点",
                    "提取.*要点",
                ],
                weight=0.9,
            ),
            TaskPattern(
                task_type=TaskType.DATA_ANALYSIS,
                patterns=[
                    "分析.*数据",
                    "统计.*信息",
                    "处理.*数据",
                    "可视化.*结果",
                    "计算.*指标",
                    "统计.*行为",
                ],
                weight=0.85,
            ),
            TaskPattern(
                task_type=TaskType.WEB_SEARCH,
                patterns=["搜索.*", "查找.*", "查询.*", "了解.*", "研究.*"],
                weight=0.8,
            ),
            TaskPattern(
                task_type=TaskType.FILE_OPERATION,
                patterns=[
                    "创建.*文件",
                    "删除.*文件",
                    "修改.*文件",
                    "读取.*文件",
                    "写入.*文件",
                ],
                weight=0.75,
            ),
            TaskPattern(
                task_type=TaskType.SYSTEM_COMMAND,
                patterns=[
                    "运行.*命令",
                    "执行.*脚本",
                    "安装.*软件",
                    "配置.*环境",
                    "部署.*服务",
                    "部署.*环境",
                ],
                weight=0.7,
            ),
        ]
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    async def detect_task_type(self, user_input: str) -> TaskType:
        """
        检测任务类型

        Args:
            user_input: 用户输入文本

        Returns:
            检测到的任务类型
        """
        try:
            # 详细检测结果
            result = await self.detect_task_type_detailed(user_input)
            return result.task_type

        except Exception as e:
            raise Exception(f"任务类型检测失败: {str(e)}")

    async def detect_task_type_detailed(self, user_input: str) -> TaskDetectionResult:
        """
        详细检测任务类型

        Args:
            user_input: 用户输入文本

        Returns:
            任务检测结果
        """
        try:
            scores: Dict[TaskType, float] = {}

            # 遍历所有模式进行匹配
            for pattern in self.patterns:
                task_type = pattern.task_type
                score = 0.0

                # 匹配模式
                for regex in pattern.patterns:
                    if re.search(regex, user_input, re.IGNORECASE):
                        score += pattern.weight

                if score > 0:
                    scores[task_type] = score

            # 计算置信度
            total_score = sum(scores.values())
            if total_score == 0:
                return TaskDetectionResult(
                    task_type=TaskType.OTHER, confidence=0.3, matched_patterns=[]
                )

            # 找到最高得分的任务类型
            best_type = max(scores.items(), key=lambda x: x[1])[0]
            best_score = scores[best_type]

            # 获取匹配的模式
            matched_patterns = []
            for pattern in self.patterns:
                if pattern.task_type == best_type:
                    for regex in pattern.patterns:
                        if re.search(regex, user_input, re.IGNORECASE):
                            matched_patterns.append(regex)

            # 计算置信度
            confidence = min(best_score / total_score, 1.0)

            return TaskDetectionResult(
                task_type=best_type,
                confidence=confidence,
                matched_patterns=matched_patterns,
            )

        except Exception as e:
            raise Exception(f"详细任务类型检测失败: {str(e)}")

    async def is_task_type(self, user_input: str, task_type: TaskType) -> bool:
        """
        判断是否是指定类型的任务

        Args:
            user_input: 用户输入文本
            task_type: 任务类型

        Returns:
            是否是指定类型的任务
        """
        result = await self.detect_task_type_detailed(user_input)
        return result.task_type == task_type

    async def get_confidence(self, user_input: str, task_type: TaskType) -> float:
        """
        获取指定任务类型的置信度

        Args:
            user_input: 用户输入文本
            task_type: 任务类型

        Returns:
            置信度 (0-1)
        """
        result = await self.detect_task_type_detailed(user_input)
        if result.task_type == task_type:
            return result.confidence
        else:
            # 计算其他任务类型的置信度
            scores: Dict[TaskType, float] = {}

            for pattern in self.patterns:
                score = 0.0
                for regex in pattern.patterns:
                    if re.search(regex, user_input, re.IGNORECASE):
                        score += pattern.weight

                if score > 0:
                    scores[pattern.task_type] = score

            total_score = sum(scores.values())
            if total_score == 0:
                return 0.0

            return scores.get(task_type, 0.0) / total_score

    async def has_multiple_matches(self, user_input: str) -> bool:
        """
        检查是否有多个任务类型匹配

        Args:
            user_input: 用户输入文本

        Returns:
            是否有多个任务类型匹配
        """
        scores: Dict[TaskType, float] = {}

        for pattern in self.patterns:
            score = 0.0
            for regex in pattern.patterns:
                if re.search(regex, user_input, re.IGNORECASE):
                    score += pattern.weight

            if score > 0:
                scores[pattern.task_type] = score

        # 如果有多个任务类型得分 > 0
        return len([score for score in scores.values() if score > 0]) > 1

    async def get_top_task_types(
        self, user_input: str, top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        获取排名前 N 的任务类型

        Args:
            user_input: 用户输入文本
            top_n: 排名数量

        Returns:
            排名前 N 的任务类型列表
        """
        scores: Dict[TaskType, float] = {}

        for pattern in self.patterns:
            score = 0.0
            for regex in pattern.patterns:
                if re.search(regex, user_input, re.IGNORECASE):
                    score += pattern.weight

            if score > 0:
                scores[pattern.task_type] = score

        # 排序
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # 计算置信度
        total_score = sum(scores.values())
        results = []
        for task_type, score in sorted_types[:top_n]:
            confidence = score / total_score if total_score > 0 else 0.0

            # 获取匹配的模式
            matched_patterns = []
            for pattern in self.patterns:
                if pattern.task_type == task_type:
                    for regex in pattern.patterns:
                        if re.search(regex, user_input, re.IGNORECASE):
                            matched_patterns.append(regex)

            results.append(
                {
                    "task_type": task_type,
                    "confidence": confidence,
                    "matched_patterns": matched_patterns,
                }
            )

        # 如果没有匹配，添加默认类型
        if not results:
            results.append(
                {"task_type": TaskType.OTHER, "confidence": 0.5, "matched_patterns": []}
            )

        return results
