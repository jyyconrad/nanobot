"""
消息分析器
============

分析消息与任务的关联：
- 语义相似度分析
- 任务相关性识别
- 决定创建新任务还是修正现有任务
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from loguru import logger

from nanobot.agent.task import Task
from nanobot.agent.task_manager import TaskManager
from nanobot.bus.events import InboundMessage


class AnalysisAction(Enum):
    """分析结果的动作类型"""

    CREATE_TASK = "create_task"  # 创建新任务
    UPDATE_TASK = "update_task"  # 更新现有任务
    CANCEL_TASK = "cancel_task"  # 取消任务
    NO_ACTION = "no_action"  # 无动作


@dataclass
class AnalysisResult:
    """消息分析结果"""

    action: AnalysisAction  # 建议的动作
    target_task_id: Optional[str]  # 目标任务ID（如果是更新或取消）
    confidence: float  # 置信度（0-1）
    reason: str  # 分析原因


class MessageAnalyzer:
    """
    消息分析器：分析消息与任务的关联关系

    主要功能：
    - 语义相似度分析
    - 任务相关性识别
    - 决定创建新任务还是修正现有任务
    """

    def __init__(self):
        self._task_manager = TaskManager()

    def analyze_message(
        self, message: InboundMessage, active_tasks: Optional[List[Task]] = None
    ) -> AnalysisResult:
        """
        分析消息与现有任务的关联

        Args:
            message: 待分析的消息
            active_tasks: 可选的活跃任务列表（如果未提供，会自动获取）

        Returns:
            分析结果对象
        """
        if active_tasks is None:
            active_tasks = self._task_manager.get_active_tasks()

        logger.debug(
            f"Analyzing message: {message.content[:50]}... against {len(active_tasks)} active tasks"
        )

        # 如果没有活跃任务，直接创建新任务
        if not active_tasks:
            logger.debug("No active tasks, suggesting create_task")
            return AnalysisResult(
                action=AnalysisAction.CREATE_TASK,
                target_task_id=None,
                confidence=1.0,
                reason="No active tasks available",
            )

        # 尝试找到与消息最相关的任务
        best_match = None
        best_score = 0.0

        for task in active_tasks:
            score = self._calculate_similarity(message.content, task.original_message)
            if score > best_score:
                best_score = score
                best_match = task

        logger.debug(f"Best matching task: {best_match.id} with score: {best_score:.2f}")

        # 根据相似度分数决定动作
        if best_score > 0.6:
            # 高相似度，建议更新任务
            logger.debug("High similarity detected, suggesting update_task")
            return AnalysisResult(
                action=AnalysisAction.UPDATE_TASK,
                target_task_id=best_match.id,
                confidence=best_score,
                reason=f"High semantic similarity ({best_score:.2f}) to existing task",
            )
        elif best_score > 0.3:
            # 中等相似度，根据消息内容判断是否需要更新
            if self._contains_correction_keywords(message.content):
                logger.debug("Correction keywords detected, suggesting update_task")
                return AnalysisResult(
                    action=AnalysisAction.UPDATE_TASK,
                    target_task_id=best_match.id,
                    confidence=best_score,
                    reason="Contains correction keywords",
                )
            else:
                logger.debug("Medium similarity but no correction keywords, suggesting create_task")
                return AnalysisResult(
                    action=AnalysisAction.CREATE_TASK,
                    target_task_id=None,
                    confidence=1.0 - best_score,
                    reason=f"Medium similarity ({best_score:.2f}) but no correction intent",
                )
        else:
            # 低相似度，创建新任务
            logger.debug("Low similarity, suggesting create_task")
            return AnalysisResult(
                action=AnalysisAction.CREATE_TASK,
                target_task_id=None,
                confidence=1.0,
                reason=f"Low similarity ({best_score:.2f}) to existing tasks",
            )

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的语义相似度（简化版实现）

        Args:
            text1: 第一个文本
            text2: 第二个文本

        Returns:
            相似度分数（0-1）
        """
        # 简化的相似度计算方法 - 实际项目中可以使用更复杂的NLP模型
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        # 计算词频交集
        common_words = words1.intersection(words2)
        return len(common_words) / min(len(words1), len(words2))

    def _contains_correction_keywords(self, text: str) -> bool:
        """
        检查文本是否包含修正关键词

        Args:
            text: 待检查的文本

        Returns:
            是否包含修正关键词
        """
        correction_keywords = [
            "修正",
            "修改",
            "更改",
            "调整",
            "重新",
            "重新做",
            "再做",
            "不对",
            "错了",
            "不正确",
            "不是",
            "重新来",
            "重来",
        ]

        lower_text = text.lower()
        for keyword in correction_keywords:
            if keyword in lower_text:
                return True
        return False

    def analyze_task_correlation(self, message: InboundMessage, task: Task) -> float:
        """
        分析消息与特定任务的关联度

        Args:
            message: 消息
            task: 任务

        Returns:
            关联度分数（0-1）
        """
        # 综合考虑多个因素的关联度
        content_similarity = self._calculate_similarity(message.content, task.original_message)

        channel_match = 1.0 if message.channel == task.channel else 0.3
        chat_id_match = 1.0 if message.chat_id == task.chat_id else 0.5

        # 计算综合得分
        score = content_similarity * 0.6 + channel_match * 0.2 + chat_id_match * 0.2

        return min(1.0, max(0.0, score))

    def find_correlated_tasks(self, message: InboundMessage, min_score: float = 0.5) -> List[dict]:
        """
        找到与消息相关的任务（分数大于等于min_score）

        Args:
            message: 待分析的消息
            min_score: 最小关联度分数

        Returns:
            相关任务列表，包含任务ID和关联度分数
        """
        active_tasks = self._task_manager.get_active_tasks()
        correlated = []

        for task in active_tasks:
            score = self.analyze_task_correlation(message, task)
            if score >= min_score:
                correlated.append({"task_id": task.id, "score": score, "task": task.to_dict()})

        # 按关联度降序排序
        return sorted(correlated, key=lambda x: x["score"], reverse=True)
