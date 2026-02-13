"""
基于规则的意图识别器

实现基于关键词匹配、正则表达式和优先级规则的意图识别功能。
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """匹配类型枚举"""

    KEYWORD = "keyword"
    REGEX = "regex"


@dataclass
class Rule:
    """规则数据类"""

    name: str
    intent: str
    pattern: str
    match_type: MatchType = MatchType.KEYWORD
    priority: int = 0
    conditions: List[Callable[[Dict[str, Any]], bool]] = field(default_factory=list)
    confidence: float = 0.8


@dataclass
class RecognitionResult:
    """识别结果数据类"""

    intent: str
    confidence: float
    rule_name: Optional[str] = None
    matched_text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        return (
            f"RecognitionResult(intent='{self.intent}', "
            f"confidence={self.confidence:.2f}, "
            f"rule_name={self.rule_name})"
        )


class RuleBasedRecognizer:
    """
    基于规则的意图识别器

    支持关键词匹配和正则表达式匹配，提供优先级机制和自定义条件判断。

    示例用法:
        >>> recognizer = RuleBasedRecognizer()
        >>> recognizer.add_rule(
        ...     name="greeting_rule",
        ...     intent="greeting",
        ...     pattern="你好|hello|hi",
        ...     match_type=MatchType.KEYWORD,
        ...     priority=10
        ... )
        >>> result = recognizer.recognize("你好，我想咨询一下")
        >>> print(result)
        RecognitionResult(intent='greeting', confidence=0.80, rule_name='greeting_rule')
    """

    def __init__(self):
        self.rules: List[Rule] = []
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        logger.debug("RuleBasedRecognizer 初始化完成")

    def add_rule(
        self,
        name: str,
        intent: str,
        pattern: str,
        match_type: MatchType = MatchType.KEYWORD,
        priority: int = 0,
        conditions: Optional[List[Callable[[Dict[str, Any]], bool]]] = None,
        confidence: float = 0.8,
    ) -> None:
        """
        添加识别规则

        Args:
            name: 规则名称
            intent: 匹配到的意图
            pattern: 匹配模式
            match_type: 匹配类型 (关键词或正则表达式)
            priority: 优先级 (值越大，优先级越高)
            conditions: 附加条件列表
            confidence: 置信度 (0-1)
        """
        if conditions is None:
            conditions = []

        rule = Rule(
            name=name,
            intent=intent,
            pattern=pattern,
            match_type=match_type,
            priority=priority,
            conditions=conditions,
            confidence=confidence,
        )

        # 编译正则表达式
        if match_type == MatchType.REGEX:
            try:
                self._compiled_patterns[name] = re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                logger.error(f"正则表达式编译失败: {pattern}, 错误: {e}")
                raise

        self.rules.append(rule)
        logger.debug(f"添加规则: {name} -> {intent}, 优先级: {priority}")

    def add_keyword_rule(
        self,
        name: str,
        intent: str,
        keywords: Union[str, List[str]],
        priority: int = 0,
        conditions: Optional[List[Callable[[Dict[str, Any]], bool]]] = None,
        confidence: float = 0.8,
    ) -> None:
        """
        添加关键词匹配规则

        Args:
            name: 规则名称
            intent: 匹配到的意图
            keywords: 关键词列表或字符串
            priority: 优先级
            conditions: 附加条件
            confidence: 置信度
        """
        if isinstance(keywords, str):
            keywords = [keywords]

        pattern = "|".join(re.escape(keyword) for keyword in keywords)
        self.add_rule(
            name=name,
            intent=intent,
            pattern=pattern,
            match_type=MatchType.KEYWORD,
            priority=priority,
            conditions=conditions,
            confidence=confidence,
        )

    def add_regex_rule(
        self,
        name: str,
        intent: str,
        regex: str,
        priority: int = 0,
        conditions: Optional[List[Callable[[Dict[str, Any]], bool]]] = None,
        confidence: float = 0.8,
    ) -> None:
        """
        添加正则表达式匹配规则

        Args:
            name: 规则名称
            intent: 匹配到的意图
            regex: 正则表达式
            priority: 优先级
            conditions: 附加条件
            confidence: 置信度
        """
        self.add_rule(
            name=name,
            intent=intent,
            pattern=regex,
            match_type=MatchType.REGEX,
            priority=priority,
            conditions=conditions,
            confidence=confidence,
        )

    def remove_rule(self, name: str) -> None:
        """
        移除规则

        Args:
            name: 规则名称
        """
        self.rules = [rule for rule in self.rules if rule.name != name]
        if name in self._compiled_patterns:
            del self._compiled_patterns[name]
        logger.debug(f"移除规则: {name}")

    def clear_rules(self) -> None:
        """清除所有规则"""
        self.rules.clear()
        self._compiled_patterns.clear()
        logger.debug("所有规则已清除")

    def recognize(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[RecognitionResult]:
        """
        识别文本的意图

        Args:
            text: 待识别的文本
            context: 上下文信息 (用于条件判断)

        Returns:
            识别结果，若未匹配到则返回 None
        """
        if context is None:
            context = {}

        logger.debug(f"开始识别文本: {text}")

        # 按优先级降序排序
        sorted_rules = sorted(self.rules, key=lambda x: x.priority, reverse=True)

        for rule in sorted_rules:
            # 检查规则条件是否满足
            if not all(cond(context) for cond in rule.conditions):
                logger.debug(f"规则 {rule.name} 条件不满足，跳过")
                continue

            matched_text = self._match_rule(rule, text)
            if matched_text:
                logger.debug(f"匹配到规则: {rule.name} -> {rule.intent}")
                return RecognitionResult(
                    intent=rule.intent,
                    confidence=rule.confidence,
                    rule_name=rule.name,
                    matched_text=matched_text,
                    metadata={
                        "match_type": rule.match_type.value,
                        "priority": rule.priority,
                    },
                )

        logger.debug("未匹配到任何规则")
        return None

    def _match_rule(self, rule: Rule, text: str) -> Optional[str]:
        """
        使用规则匹配文本

        Args:
            rule: 匹配规则
            text: 待匹配文本

        Returns:
            匹配到的文本，若未匹配到则返回 None
        """
        if rule.match_type == MatchType.KEYWORD:
            return self._match_keywords(rule.pattern, text)
        elif rule.match_type == MatchType.REGEX:
            return self._match_regex(rule.name, text)
        else:
            logger.warning(f"未知的匹配类型: {rule.match_type}")
            return None

    def _match_keywords(self, pattern: str, text: str) -> Optional[str]:
        """
        关键词匹配

        Args:
            pattern: 关键词模式 (使用 | 分隔)
            text: 待匹配文本

        Returns:
            匹配到的文本，若未匹配到则返回 None
        """
        regex_pattern = rf"({pattern})"
        match = re.search(regex_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _match_regex(self, rule_name: str, text: str) -> Optional[str]:
        """
        正则表达式匹配

        Args:
            rule_name: 规则名称
            text: 待匹配文本

        Returns:
            匹配到的文本，若未匹配到则返回 None
        """
        if rule_name not in self._compiled_patterns:
            logger.warning(f"规则 {rule_name} 的正则表达式未编译")
            return None

        regex = self._compiled_patterns[rule_name]
        match = regex.search(text)
        if match:
            return match.group(0)
        return None

    def recognize_all(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> List[RecognitionResult]:
        """
        识别文本的所有匹配意图 (按优先级排序)

        Args:
            text: 待识别的文本
            context: 上下文信息

        Returns:
            所有匹配到的识别结果列表
        """
        if context is None:
            context = {}

        results = []
        for rule in self.rules:
            if all(cond(context) for cond in rule.conditions):
                matched_text = self._match_rule(rule, text)
                if matched_text:
                    results.append(
                        RecognitionResult(
                            intent=rule.intent,
                            confidence=rule.confidence,
                            rule_name=rule.name,
                            matched_text=matched_text,
                            metadata={
                                "match_type": rule.match_type.value,
                                "priority": rule.priority,
                            },
                        )
                    )

        # 按优先级降序排序
        results.sort(key=lambda x: x.metadata.get("priority", 0), reverse=True)

        logger.debug(f"匹配到 {len(results)} 个结果")
        return results

    def load_rules_from_config(self, config: List[Dict[str, Any]]) -> None:
        """
        从配置加载规则

        Args:
            config: 规则配置列表
        """
        for rule_config in config:
            match_type = MatchType(rule_config.get("match_type", "keyword"))
            self.add_rule(
                name=rule_config["name"],
                intent=rule_config["intent"],
                pattern=rule_config["pattern"],
                match_type=match_type,
                priority=rule_config.get("priority", 0),
                conditions=rule_config.get("conditions", []),
                confidence=rule_config.get("confidence", 0.8),
            )
        logger.debug(f"从配置加载了 {len(config)} 个规则")

    @property
    def rule_count(self) -> int:
        """规则数量"""
        return len(self.rules)

    def __repr__(self):
        return f"RuleBasedRecognizer(rules={self.rule_count})"
