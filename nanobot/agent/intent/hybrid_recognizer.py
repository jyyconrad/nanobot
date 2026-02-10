"""
综合意图识别器

整合三层识别器（规则、代码、LLM），实现优先级机制、降级策略和结果合并。
"""

import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Dict, Any, Union, Tuple
from enum import Enum

from nanobot.agent.intent.rule_based_recognizer import (
    RuleBasedRecognizer,
    RecognitionResult as RuleResult
)
from nanobot.agent.intent.code_based_recognizer import (
    CodeBasedRecognizer,
    CodeRecognitionResult as CodeResult
)
from nanobot.agent.intent.llm_recognizer import (
    LLMRecognizer,
    LLMRecognitionResult as LLMResult,
    LLMProvider
)

logger = logging.getLogger(__name__)


class RecognizerType(Enum):
    """识别器类型枚举"""
    RULE = "rule"
    CODE = "code"
    LLM = "llm"


@dataclass
class HybridRecognitionResult:
    """综合识别结果数据类"""
    intent: str
    confidence: float
    recognizer_type: RecognizerType
    source_result: Union[RuleResult, CodeResult, LLMResult]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        return (f"HybridRecognitionResult(intent='{self.intent}', "
                f"confidence={self.confidence:.2f}, "
                f"type={self.recognizer_type.value})")


@dataclass
class FallbackConfig:
    """降级策略配置"""
    enabled: bool = True
    min_confidence: float = 0.5
    fallback_order: List[RecognizerType] = field(default_factory=lambda: [
        RecognizerType.RULE,
        RecognizerType.CODE,
        RecognizerType.LLM
    ])


@dataclass
class ConflictResolutionConfig:
    """冲突处理配置"""
    strategy: str = "priority"  # priority, confidence, voting
    min_confidence_diff: float = 0.1


class HybridRecognizer:
    """
    综合意图识别器

    整合三层识别器（规则 > 代码 > LLM），支持优先级机制、降级策略和冲突处理。

    示例用法:
        >>> from nanobot.agent.intent import HybridRecognizer
        >>> recognizer = HybridRecognizer()
        >>> recognizer.rule_recognizer.add_keyword_rule(
        ...     "greeting", "greeting", ["你好", "hello"]
        ... )
        >>> result = recognizer.recognize("你好，有什么可以帮您？")
        >>> print(result)
        HybridRecognitionResult(intent='greeting', confidence=0.80, type='rule')
    """

    def __init__(
        self,
        fallback_config: Optional[FallbackConfig] = None,
        conflict_config: Optional[ConflictResolutionConfig] = None
    ):
        self.rule_recognizer = RuleBasedRecognizer()
        self.code_recognizer = CodeBasedRecognizer()
        self.llm_recognizer = LLMRecognizer()

        self.fallback_config = fallback_config or FallbackConfig()
        self.conflict_config = conflict_config or ConflictResolutionConfig()

        self._result_processors: List[
            Callable[[List[HybridRecognitionResult]], List[HybridRecognitionResult]]
        ] = []

        logger.debug("HybridRecognizer 初始化完成")

    def add_result_processor(
        self,
        processor: Callable[[List[HybridRecognitionResult]], List[HybridRecognitionResult]]
    ) -> None:
        """
        添加结果处理器

        Args:
            processor: 结果处理函数
        """
        self._result_processors.append(processor)
        logger.debug("结果处理器已添加")

    def recognize(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[HybridRecognitionResult]:
        """
        识别文本的意图（主入口方法）

        Args:
            text: 待识别的文本
            context: 上下文信息

        Returns:
            综合识别结果，若所有识别器都失败则返回 None
        """
        if context is None:
            context = {}

        logger.debug(f"开始综合识别文本: {text}")

        # 执行识别
        results = self._execute_all_recognizers(text, context)

        # 应用结果处理器
        processed_results = self._apply_processors(results)

        # 冲突处理和最终结果选择
        final_result = self._resolve_conflicts(processed_results)

        if final_result:
            logger.debug(f"最终识别结果: {final_result}")
            return final_result

        logger.debug("所有识别器都未能返回有效结果")
        return None

    def _execute_all_recognizers(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> List[HybridRecognitionResult]:
        """
        执行所有识别器

        Args:
            text: 待识别文本
            context: 上下文信息

        Returns:
            所有识别器的结果列表
        """
        results = []

        # 规则识别
        rule_result = self.rule_recognizer.recognize(text, context)
        if rule_result:
            results.append(
                HybridRecognitionResult(
                    intent=rule_result.intent,
                    confidence=rule_result.confidence,
                    recognizer_type=RecognizerType.RULE,
                    source_result=rule_result,
                    metadata={
                        "rule_name": rule_result.rule_name,
                        "match_type": rule_result.metadata.get("match_type")
                    }
                )
            )

        # 代码识别
        code_result = self.code_recognizer.recognize(text, context)
        if code_result:
            results.append(
                HybridRecognitionResult(
                    intent=code_result.intent,
                    confidence=code_result.confidence,
                    recognizer_type=RecognizerType.CODE,
                    source_result=code_result,
                    metadata=code_result.metadata
                )
            )

        # LLM 识别
        llm_result = self.llm_recognizer.recognize(text, context)
        if llm_result:
            results.append(
                HybridRecognitionResult(
                    intent=llm_result.intent,
                    confidence=llm_result.confidence,
                    recognizer_type=RecognizerType.LLM,
                    source_result=llm_result,
                    metadata={"reasoning": llm_result.reasoning}
                )
            )

        logger.debug(f"各识别器结果: {[repr(r) for r in results]}")
        return results

    def _apply_processors(
        self,
        results: List[HybridRecognitionResult]
    ) -> List[HybridRecognitionResult]:
        """
        应用结果处理器

        Args:
            results: 原始结果列表

        Returns:
            处理后的结果列表
        """
        processed = results.copy()
        for processor in self._result_processors:
            try:
                processed = processor(processed)
            except Exception as e:
                logger.error(f"结果处理器执行失败: {e}", exc_info=True)

        return processed

    def _resolve_conflicts(
        self,
        results: List[HybridRecognitionResult]
    ) -> Optional[HybridRecognitionResult]:
        """
        冲突处理和结果选择

        Args:
            results: 识别结果列表

        Returns:
            最终结果
        """
        if not results:
            return None

        strategy = self.conflict_config.strategy

        if strategy == "priority":
            return self._resolve_by_priority(results)
        elif strategy == "confidence":
            return self._resolve_by_confidence(results)
        elif strategy == "voting":
            return self._resolve_by_voting(results)
        else:
            logger.warning(f"未知的冲突处理策略: {strategy}，使用默认策略")
            return self._resolve_by_priority(results)

    def _resolve_by_priority(
        self,
        results: List[HybridRecognitionResult]
    ) -> Optional[HybridRecognitionResult]:
        """
        按识别器优先级解析冲突

        Args:
            results: 结果列表

        Returns:
            最终结果
        """
        # 优先级：规则 > 代码 > LLM
        priority_order = [
            RecognizerType.RULE,
            RecognizerType.CODE,
            RecognizerType.LLM
        ]

        for recognizer_type in priority_order:
            for result in results:
                if (result.recognizer_type == recognizer_type and
                        result.confidence >= self.fallback_config.min_confidence):
                    return result

        # 降级到任何有效结果
        if self.fallback_config.enabled:
            for recognizer_type in self.fallback_config.fallback_order:
                for result in results:
                    if result.recognizer_type == recognizer_type:
                        return result

        return None

    def _resolve_by_confidence(
        self,
        results: List[HybridRecognitionResult]
    ) -> Optional[HybridRecognitionResult]:
        """
        按置信度解析冲突

        Args:
            results: 结果列表

        Returns:
            最终结果
        """
        sorted_results = sorted(
            results,
            key=lambda x: x.confidence,
            reverse=True
        )

        best_result = sorted_results[0]

        if best_result.confidence >= self.fallback_config.min_confidence:
            return best_result

        if self.fallback_config.enabled:
            for result in sorted_results:
                if result.confidence > 0:
                    return result

        return None

    def _resolve_by_voting(
        self,
        results: List[HybridRecognitionResult]
    ) -> Optional[HybridRecognitionResult]:
        """
        按投票解析冲突

        Args:
            results: 结果列表

        Returns:
            最终结果
        """
        intent_counts: Dict[str, Tuple[int, float]] = {}

        for result in results:
            if result.confidence >= self.fallback_config.min_confidence:
                if result.intent in intent_counts:
                    count, total_confidence = intent_counts[result.intent]
                    intent_counts[result.intent] = (count + 1, total_confidence + result.confidence)
                else:
                    intent_counts[result.intent] = (1, result.confidence)

        if intent_counts:
            # 选择投票数最多的意图
            best_intent = max(
                intent_counts.items(),
                key=lambda x: (x[1][0], x[1][1])
            )
            # 找到对应的结果
            for result in results:
                if result.intent == best_intent[0]:
                    return result

        return None

    def recognize_with_fallback(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[HybridRecognitionResult]:
        """
        使用降级策略识别文本意图

        Args:
            text: 待识别的文本
            context: 上下文信息

        Returns:
            识别结果（包含降级策略）
        """
        return self.recognize(text, context)

    def get_all_results(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[HybridRecognitionResult]:
        """
        获取所有识别器的结果（不进行冲突处理）

        Args:
            text: 待识别的文本
            context: 上下文信息

        Returns:
            所有识别器的结果列表
        """
        if context is None:
            context = {}

        return self._execute_all_recognizers(text, context)

    def set_llm_config(
        self,
        provider: LLMProvider,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> None:
        """
        设置 LLM 配置

        Args:
            provider: LLM 提供商
            api_key: API 密钥
            model: 模型名称
            base_url: 底座地址
        """
        self.llm_recognizer = LLMRecognizer(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url
        )
        logger.debug(
            f"LLM 配置已更新: provider={provider.value}, model={model}"
        )

    def __repr__(self):
        return (f"HybridRecognizer("
                f"rules={self.rule_recognizer.rule_count}, "
                f"code_rules={self.code_recognizer.rule_count}, "
                f"llm_samples={self.llm_recognizer.sample_count})")
