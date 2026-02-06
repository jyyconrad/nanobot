"""
复杂度分析器

负责评估任务的复杂度，为任务规划提供依据。
"""

import asyncio
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from nanobot.agent.planner.models import TaskType, ComplexityFeature, ComplexityAnalysis


class ComplexityAnalyzer(BaseModel):
    """复杂度分析器"""
    # 任务类型复杂度基础权重
    type_weights: Dict[TaskType, float] = Field(default_factory=lambda: {
        TaskType.CODE_GENERATION: 0.92,
        TaskType.DATA_ANALYSIS: 0.9,
        TaskType.TEXT_SUMMARIZATION: 0.75,
        TaskType.WEB_SEARCH: 0.55,
        TaskType.FILE_OPERATION: 0.45,
        TaskType.SYSTEM_COMMAND: 0.85,
        TaskType.OTHER: 0.3
    })

    # 文本特征
    text_features: List[ComplexityFeature] = Field(default_factory=lambda: [
        ComplexityFeature(name="length", weight=0.998, score=0.0),
        ComplexityFeature(name="vocabulary", weight=0.0015, score=0.0),
        ComplexityFeature(name="sentence_structure", weight=0.00025, score=0.0),
        ComplexityFeature(name="domain_terms", weight=0.000125, score=0.0),
        ComplexityFeature(name="ambiguity", weight=0.000125, score=0.0)
    ])

    # 领域术语列表
    domain_terms: Dict[TaskType, List[str]] = Field(default_factory=lambda: {
        TaskType.CODE_GENERATION: ["class", "function", "algorithm", "optimization", "refactor"],
        TaskType.DATA_ANALYSIS: ["statistical", "regression", "classification", "clustering", "hypothesis"],
        TaskType.TEXT_SUMMARIZATION: ["abstract", "summary", "synthesize", "extract", "key points"],
        TaskType.WEB_SEARCH: ["research", "latest", "comprehensive", "compare", "analyze"],
        TaskType.FILE_OPERATION: ["batch", "recursive", "backup", "restore", "encrypt"],
        TaskType.SYSTEM_COMMAND: ["install", "configure", "deploy", "monitor", "troubleshoot"]
    })

    class Config:
        """配置类"""
        arbitrary_types_allowed = True

    async def analyze_complexity(self, user_input: str, task_type: TaskType) -> float:
        """
        分析任务复杂度

        Args:
            user_input: 用户输入文本
            task_type: 任务类型

        Returns:
            复杂度评分 (0-1)
        """
        try:
            # 基础复杂度
            base_complexity = self.type_weights.get(task_type, 0.3)

            # 文本复杂度特征得分
            text_score = await self._analyze_text_features(user_input, task_type)

            # 综合得分
            total_score = (base_complexity * 0.6 + text_score * 0.4)

            # 确保得分在 0-1 范围内
            return max(0.0, min(1.0, total_score))

        except Exception as e:
            raise Exception(f"复杂度分析失败: {str(e)}")

    async def analyze_detailed(self, user_input: str, task_type: TaskType) -> ComplexityAnalysis:
        """
        详细分析任务复杂度

        Args:
            user_input: 用户输入文本
            task_type: 任务类型

        Returns:
            复杂度分析结果
        """
        try:
            # 基础复杂度
            base_complexity = self.type_weights.get(task_type, 0.3)

            # 文本复杂度特征得分
            text_features = await self._analyze_text_features_detailed(user_input, task_type)

            # 综合得分
            total_score = (base_complexity * 0.6 + sum(f.score * f.weight for f in text_features) * 0.4)
            total_score = max(0.0, min(1.0, total_score))

            # 生成解释
            explanation = await self._generate_explanation(task_type, text_features)

            return ComplexityAnalysis(
                total_score=total_score,
                features=text_features,
                explanation=explanation
            )

        except Exception as e:
            raise Exception(f"详细复杂度分析失败: {str(e)}")

    async def _analyze_text_features(self, user_input: str, task_type: TaskType) -> float:
        """
        分析文本特征复杂度

        Args:
            user_input: 用户输入文本
            task_type: 任务类型

        Returns:
            文本特征得分 (0-1)
        """
        features = await self._analyze_text_features_detailed(user_input, task_type)
        return sum(f.score * f.weight for f in features)

    async def _analyze_text_features_detailed(self, user_input: str, task_type: TaskType) -> List[ComplexityFeature]:
        """
        详细分析文本特征复杂度

        Args:
            user_input: 用户输入文本
            task_type: 任务类型

        Returns:
            文本特征得分列表
        """
        features = []

        # 长度特征
        length = len(user_input)
        length_score = min(length / 300, 1.0)  # 300 字符以上为高复杂度
        features.append(ComplexityFeature(name="length", weight=0.2, score=length_score))

        # 词汇复杂度
        words = user_input.split()
        unique_words = set(words)
        vocabulary_score = min(len(unique_words) / 50, 1.0)  # 50 个不同词汇以上为高复杂度
        features.append(ComplexityFeature(name="vocabulary", weight=0.15, score=vocabulary_score))

        # 句子结构复杂度（基于标点符号数量）
        punctuation_count = len(re.findall(r'[.,!?;()]', user_input))
        sentence_score = min(punctuation_count / 10, 1.0)  # 10 个以上标点为高复杂度
        features.append(ComplexityFeature(name="sentence_structure", weight=0.15, score=sentence_score))

        # 领域术语特征
        domain_terms = self.domain_terms.get(task_type, [])
        term_count = sum(1 for term in domain_terms if term.lower() in user_input.lower())
        domain_score = min(term_count / 3, 1.0)  # 3 个以上领域术语为高复杂度
        features.append(ComplexityFeature(name="domain_terms", weight=0.2, score=domain_score))

        # 歧义特征
        ambiguity_count = sum(1 for word in ["可能", "大概", "或许", "应该", "可能需要"] if word in user_input)
        ambiguity_score = min(ambiguity_count / 3, 1.0)  # 3 个以上模糊词汇为高复杂度
        features.append(ComplexityFeature(name="ambiguity", weight=0.3, score=ambiguity_score))

        return features

    async def _generate_explanation(self, task_type: TaskType, features: List[ComplexityFeature]) -> str:
        """
        生成复杂度解释

        Args:
            task_type: 任务类型
            features: 文本特征得分

        Returns:
            复杂度解释
        """
        explanations = []

        # 任务类型解释
        type_weight = self.type_weights.get(task_type, 0.3)
        explanations.append(f"任务类型 '{task_type}' 基础复杂度为 {type_weight:.2f}")

        # 文本特征解释
        for feature in features:
            if feature.score > 0.5:
                explanations.append(f"{feature.name}特征复杂度较高 ({feature.score:.2f})")

        return "; ".join(explanations)

    async def is_complex(self, user_input: str, task_type: TaskType, threshold: float = 0.6) -> bool:
        """
        判断任务是否复杂

        Args:
            user_input: 用户输入文本
            task_type: 任务类型
            threshold: 复杂度阈值

        Returns:
            是否为复杂任务
        """
        complexity = await self.analyze_complexity(user_input, task_type)
        return complexity > threshold

    async def get_complexity_category(self, user_input: str, task_type: TaskType) -> str:
        """
        获取复杂度类别

        Args:
            user_input: 用户输入文本
            task_type: 任务类型

        Returns:
            复杂度类别
        """
        complexity = await self.analyze_complexity(user_input, task_type)

        if complexity >= 0.65:
            return "非常复杂"
        elif complexity >= 0.56:
            return "复杂"
        elif complexity >= 0.5:
            return "中等"
        elif complexity >= 0.05:
            return "简单"
        else:
            return "非常简单"
