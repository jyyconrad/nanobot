"""
基于代码逻辑的意图识别器

实现基于函数回调、自定义判断逻辑和复杂条件组合的意图识别功能。
"""

import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Dict, Any, Union

logger = logging.getLogger(__name__)


@dataclass
class CodeRule:
    """代码规则数据类"""
    name: str
    intent: str
    predicate: Callable[[str, Dict[str, Any]], bool]
    confidence: float = 0.9
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeRecognitionResult:
    """代码识别结果数据类"""
    intent: str
    confidence: float
    rule_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        return (f"CodeRecognitionResult(intent='{self.intent}', "
                f"confidence={self.confidence:.2f}, "
                f"rule_name={self.rule_name})")


class CodeBasedRecognizer:
    """
    基于代码逻辑的意图识别器

    支持函数回调、自定义判断逻辑和复杂条件组合的意图识别。

    示例用法:
        >>> def is_weather_query(text, context):
        ...     return "天气" in text and len(text) < 50
        ...
        >>> recognizer = CodeBasedRecognizer()
        >>> recognizer.add_rule(
        ...     name="weather_rule",
        ...     intent="weather.query",
        ...     predicate=is_weather_query,
        ...     confidence=0.95,
        ...     priority=5
        ... )
        >>> result = recognizer.recognize("今天北京的天气怎么样？")
        >>> print(result)
        CodeRecognitionResult(intent='weather.query', confidence=0.95, rule_name='weather_rule')
    """

    def __init__(self):
        self.rules: List[CodeRule] = []
        logger.debug("CodeBasedRecognizer 初始化完成")

    def add_rule(
        self,
        name: str,
        intent: str,
        predicate: Callable[[str, Dict[str, Any]], bool],
        confidence: float = 0.9,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        添加代码规则

        Args:
            name: 规则名称
            intent: 匹配到的意图
            predicate: 断言函数，返回 True 表示匹配成功
            confidence: 置信度 (0-1)
            priority: 优先级 (值越大，优先级越高)
            metadata: 元数据
        """
        if metadata is None:
            metadata = {}

        rule = CodeRule(
            name=name,
            intent=intent,
            predicate=predicate,
            confidence=confidence,
            priority=priority,
            metadata=metadata
        )

        self.rules.append(rule)
        logger.debug(f"添加代码规则: {name} -> {intent}, 优先级: {priority}")

    def remove_rule(self, name: str) -> None:
        """
        移除规则

        Args:
            name: 规则名称
        """
        self.rules = [rule for rule in self.rules if rule.name != name]
        logger.debug(f"移除代码规则: {name}")

    def clear_rules(self) -> None:
        """清除所有规则"""
        self.rules.clear()
        logger.debug("所有代码规则已清除")

    def recognize(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[CodeRecognitionResult]:
        """
        识别文本的意图

        Args:
            text: 待识别的文本
            context: 上下文信息

        Returns:
            识别结果，若未匹配到则返回 None
        """
        if context is None:
            context = {}

        logger.debug(f"开始识别文本: {text}")

        # 按优先级降序排序
        sorted_rules = sorted(
            self.rules,
            key=lambda x: x.priority,
            reverse=True
        )

        for rule in sorted_rules:
            try:
                if rule.predicate(text, context):
                    logger.debug(f"匹配到代码规则: {rule.name} -> {rule.intent}")
                    return CodeRecognitionResult(
                        intent=rule.intent,
                        confidence=rule.confidence,
                        rule_name=rule.name,
                        metadata=rule.metadata
                    )
            except Exception as e:
                logger.error(
                    f"规则 {rule.name} 执行失败: {e}",
                    exc_info=True
                )

        logger.debug("未匹配到任何代码规则")
        return None

    def recognize_all(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[CodeRecognitionResult]:
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
            try:
                if rule.predicate(text, context):
                    results.append(
                        CodeRecognitionResult(
                            intent=rule.intent,
                            confidence=rule.confidence,
                            rule_name=rule.name,
                            metadata=rule.metadata
                        )
                    )
            except Exception as e:
                logger.error(
                    f"规则 {rule.name} 执行失败: {e}",
                    exc_info=True
                )

        # 按优先级降序排序
        results.sort(
            key=lambda x: x.metadata.get("priority", 0)
            if "priority" in x.metadata
            else [r for r in self.rules if r.name == x.rule_name][0].priority
            if x.rule_name
            else 0,
            reverse=True
        )

        logger.debug(f"匹配到 {len(results)} 个代码规则结果")
        return results

    def add_condition_rule(
        self,
        name: str,
        intent: str,
        conditions: List[Callable[[str, Dict[str, Any]], bool]],
        operator: Callable[[List[bool]], bool] = all,
        confidence: float = 0.85,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        添加条件组合规则

        Args:
            name: 规则名称
            intent: 匹配到的意图
            conditions: 条件列表
            operator: 条件组合操作符 (all 或 any)
            confidence: 置信度
            priority: 优先级
            metadata: 元数据
        """
        def predicate(text: str, context: Dict[str, Any]) -> bool:
            return operator(cond(text, context) for cond in conditions)

        self.add_rule(
            name=name,
            intent=intent,
            predicate=predicate,
            confidence=confidence,
            priority=priority,
            metadata=metadata
        )

    def add_keyword_condition_rule(
        self,
        name: str,
        intent: str,
        keywords: List[str],
        operator: Callable[[List[bool]], bool] = any,
        confidence: float = 0.85,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        添加关键词条件规则

        Args:
            name: 规则名称
            intent: 匹配到的意图
            keywords: 关键词列表
            operator: 条件组合操作符 (all 或 any)
            confidence: 置信度
            priority: 优先级
            metadata: 元数据
        """
        def predicate(text: str, context: Dict[str, Any]) -> bool:
            return operator(keyword in text.lower() for keyword in keywords)

        self.add_rule(
            name=name,
            intent=intent,
            predicate=predicate,
            confidence=confidence,
            priority=priority,
            metadata=metadata
        )

    def add_length_rule(
        self,
        name: str,
        intent: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        confidence: float = 0.8,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        添加文本长度规则

        Args:
            name: 规则名称
            intent: 匹配到的意图
            min_length: 最小长度
            max_length: 最大长度
            confidence: 置信度
            priority: 优先级
            metadata: 元数据
        """
        def predicate(text: str, context: Dict[str, Any]) -> bool:
            length = len(text)
            if min_length is not None and length < min_length:
                return False
            if max_length is not None and length > max_length:
                return False
            return True

        self.add_rule(
            name=name,
            intent=intent,
            predicate=predicate,
            confidence=confidence,
            priority=priority,
            metadata=metadata
        )

    def add_context_rule(
        self,
        name: str,
        intent: str,
        context_key: str,
        context_value: Any,
        confidence: float = 0.85,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        添加上下文规则

        Args:
            name: 规则名称
            intent: 匹配到的意图
            context_key: 上下文键
            context_value: 上下文值
            confidence: 置信度
            priority: 优先级
            metadata: 元数据
        """
        def predicate(text: str, context: Dict[str, Any]) -> bool:
            return context.get(context_key) == context_value

        self.add_rule(
            name=name,
            intent=intent,
            predicate=predicate,
            confidence=confidence,
            priority=priority,
            metadata=metadata
        )

    @property
    def rule_count(self) -> int:
        """规则数量"""
        return len(self.rules)

    def __repr__(self):
        return (f"CodeBasedRecognizer(rules={self.rule_count})")
