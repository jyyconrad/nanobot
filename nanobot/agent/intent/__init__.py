"""
意图识别模块

提供三层意图识别系统：
- RuleBasedRecognizer: 基于规则的识别
- CodeBasedRecognizer: 基于代码逻辑的识别
- LLMRecognizer: 基于大模型的识别
- HybridRecognizer: 综合识别器（整合三层识别器）

使用示例：
    >>> from nanobot.agent.intent import HybridRecognizer, MatchType
    >>> recognizer = HybridRecognizer()
    >>> recognizer.rule_recognizer.add_keyword_rule(
    ...     "greeting", "greeting", ["你好", "hello"]
    ... )
    >>> result = recognizer.recognize("你好，有什么可以帮您？")
    >>> print(result)
    HybridRecognitionResult(intent='greeting', confidence=0.80, type='rule')
"""

from .rule_based_recognizer import (
    RuleBasedRecognizer,
    MatchType,
    Rule,
    RecognitionResult
)

from .code_based_recognizer import (
    CodeBasedRecognizer,
    CodeRule,
    CodeRecognitionResult
)

from .llm_recognizer import (
    LLMRecognizer,
    LLMProvider,
    LLMSample,
    LLMRecognitionResult,
    LLMClient,
    MockLLMClient
)

from .hybrid_recognizer import (
    HybridRecognizer,
    RecognizerType,
    HybridRecognitionResult,
    FallbackConfig,
    ConflictResolutionConfig
)

__all__ = [
    # 规则识别器
    "RuleBasedRecognizer",
    "MatchType",
    "Rule",
    "RecognitionResult",

    # 代码识别器
    "CodeBasedRecognizer",
    "CodeRule",
    "CodeRecognitionResult",

    # LLM 识别器
    "LLMRecognizer",
    "LLMProvider",
    "LLMSample",
    "LLMRecognitionResult",
    "LLMClient",
    "MockLLMClient",

    # 综合识别器
    "HybridRecognizer",
    "RecognizerType",
    "HybridRecognitionResult",
    "FallbackConfig",
    "ConflictResolutionConfig"
]
