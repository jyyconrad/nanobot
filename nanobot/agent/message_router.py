"""
消息路由器模块 - 负责将消息路由到合适的处理器

该模块提供了 MessageRouter 类，用于基于规则的消息路由，
支持处理器的注册、注销和路由管理功能。
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .message_analyzer import AnalysisResult, MessageAnalyzer

# 配置日志记录
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class RouteMatchType(Enum):
    """
    路由匹配类型枚举
    """

    EXACT = "exact"
    CONTAINS = "contains"
    REGEX = "regex"
    INTENT = "intent"
    KEYWORD = "keyword"


@dataclass
class RouteRule:
    """
    路由规则数据类
    """

    name: str
    match_type: RouteMatchType
    match_value: Union[str, List[str]]
    handler: Callable[[Dict[str, Any]], Any]
    priority: int = 0
    condition: Optional[Callable[[AnalysisResult], bool]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MessageRouter:
    """
    消息路由器类

    负责根据预定义规则将消息路由到合适的处理器，
    支持多种匹配方式和优先级管理。
    """

    def __init__(self, analyzer: Optional[MessageAnalyzer] = None):
        """
        初始化消息路由器

        Args:
            analyzer: 消息分析器实例，用于消息分析
        """
        self.logger = logger
        self.analyzer = analyzer or MessageAnalyzer()
        self.routes: List[RouteRule] = []
        self.default_handler: Optional[Callable[[Dict[str, Any]], Any]] = None
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

    def register_handler(self, name: str, handler: Callable[[Dict[str, Any]], Any]):
        """
        注册消息处理器

        Args:
            name: 处理器名称（唯一标识符）
            handler: 处理器函数
        """
        self.handlers[name] = handler
        self.logger.debug(f"注册处理器: {name}")

    def unregister_handler(
        self, name: str
    ) -> Optional[Callable[[Dict[str, Any]], Any]]:
        """
        注销消息处理器

        Args:
            name: 处理器名称

        Returns:
            被注销的处理器函数，如果不存在则返回 None
        """
        handler = self.handlers.pop(name, None)
        if handler:
            self.logger.debug(f"注销处理器: {name}")

            # 同时从路由规则中移除使用该处理器的规则
            self.routes = [route for route in self.routes if route.handler != handler]

        return handler

    def add_route(self, rule: RouteRule):
        """
        添加路由规则

        Args:
            rule: 路由规则对象
        """
        self.routes.append(rule)
        self.routes.sort(key=lambda x: x.priority, reverse=True)
        self.logger.debug(f"添加路由规则: {rule.name} (优先级: {rule.priority})")

    def remove_route(self, name: str) -> Optional[RouteRule]:
        """
        移除路由规则

        Args:
            name: 路由规则名称

        Returns:
            被移除的路由规则，如果不存在则返回 None
        """
        for i, route in enumerate(self.routes):
            if route.name == name:
                removed_rule = self.routes.pop(i)
                self.logger.debug(f"移除路由规则: {name}")
                return removed_rule
        return None

    def set_default_handler(self, handler: Callable[[Dict[str, Any]], Any]):
        """
        设置默认处理器

        当没有任何规则匹配时使用此处理器

        Args:
            handler: 默认处理器函数
        """
        self.default_handler = handler
        self.logger.debug("设置默认处理器")

    def route_message(self, message: Dict[str, Any]) -> Any:
        """
        路由消息到合适的处理器

        Args:
            message: 要路由的消息字典

        Returns:
            处理器的返回结果
        """
        self.logger.debug(f"路由消息: {message}")

        # 分析消息
        text = message.get("text", "")
        analysis = self.analyzer.analyze(text, message.get("metadata"))

        # 查找匹配的路由规则
        matched_route: Optional[RouteRule] = None

        for route in self.routes:
            if self._match_route(route, analysis):
                matched_route = route
                self.logger.debug(f"匹配到路由规则: {route.name}")
                break

        # 执行处理
        if matched_route:
            try:
                result = matched_route.handler(
                    {"message": message, "analysis": analysis, "route": matched_route}
                )
                self.logger.info(f"路由处理完成: {matched_route.name}")
                return result
            except Exception as e:
                self.logger.error(f"路由处理失败: {matched_route.name}, 错误: {e}")

        # 使用默认处理器
        if self.default_handler:
            try:
                result = self.default_handler(
                    {"message": message, "analysis": analysis}
                )
                self.logger.info("使用默认处理器处理消息")
                return result
            except Exception as e:
                self.logger.error(f"默认处理器失败: {e}")

        self.logger.warning("没有找到匹配的路由规则和默认处理器")
        return None

    def _match_route(self, route: RouteRule, analysis: AnalysisResult) -> bool:
        """
        检查路由规则是否匹配分析结果

        Args:
            route: 路由规则
            analysis: 消息分析结果

        Returns:
            匹配成功返回 True，否则返回 False
        """
        # 检查条件
        if route.condition and not route.condition(analysis):
            return False

        match_value = route.match_value

        # 根据匹配类型检查
        if route.match_type == RouteMatchType.EXACT:
            return analysis.raw_text == match_value

        elif route.match_type == RouteMatchType.CONTAINS:
            if isinstance(match_value, str):
                return match_value in analysis.raw_text
            elif isinstance(match_value, list):
                return any(v in analysis.raw_text for v in match_value)

        elif route.match_type == RouteMatchType.REGEX:
            import re

            if isinstance(match_value, str):
                return (
                    re.search(match_value, analysis.raw_text, re.IGNORECASE) is not None
                )
            elif isinstance(match_value, list):
                return any(
                    re.search(v, analysis.raw_text, re.IGNORECASE) for v in match_value
                )

        elif route.match_type == RouteMatchType.INTENT:
            if isinstance(match_value, str):
                return analysis.intent == match_value
            elif isinstance(match_value, list):
                return analysis.intent in match_value

        elif route.match_type == RouteMatchType.KEYWORD:
            if isinstance(match_value, str):
                return match_value in analysis.keywords
            elif isinstance(match_value, list):
                return any(v in analysis.keywords for v in match_value)

        return False

    def create_route(
        self,
        name: str,
        match_type: Union[RouteMatchType, str],
        match_value: Union[str, List[str]],
        handler: Union[str, Callable[[Dict[str, Any]], Any]],
        priority: int = 0,
        condition: Optional[Callable[[AnalysisResult], bool]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RouteRule:
        """
        快速创建并添加路由规则

        Args:
            name: 路由规则名称
            match_type: 匹配类型（字符串或枚举）
            match_value: 匹配值
            handler: 处理器（名称或函数）
            priority: 优先级
            condition: 匹配条件
            metadata: 元数据

        Returns:
            创建的路由规则对象
        """
        # 解析匹配类型
        if isinstance(match_type, str):
            match_type = RouteMatchType(match_type.lower())

        # 解析处理器
        if isinstance(handler, str):
            if handler not in self.handlers:
                raise ValueError(f"处理器 '{handler}' 未注册")
            handler = self.handlers[handler]

        rule = RouteRule(
            name=name,
            match_type=match_type,
            match_value=match_value,
            handler=handler,
            priority=priority,
            condition=condition,
            metadata=metadata or {},
        )

        self.add_route(rule)
        return rule

    def get_routes(self) -> List[RouteRule]:
        """
        获取所有路由规则列表

        Returns:
            路由规则列表（按优先级排序）
        """
        return self.routes.copy()

    def get_handlers(self) -> Dict[str, Callable[[Dict[str, Any]], Any]]:
        """
        获取所有注册的处理器

        Returns:
            处理器字典
        """
        return self.handlers.copy()

    def clear_routes(self):
        """
        清除所有路由规则
        """
        self.routes.clear()
        self.logger.debug("清除所有路由规则")

    def import_rules(self, rules_config: List[Dict[str, Any]]):
        """
        从配置导入路由规则

        Args:
            rules_config: 路由规则配置列表
        """
        for config in rules_config:
            try:
                self.create_route(
                    name=config["name"],
                    match_type=config["match_type"],
                    match_value=config["match_value"],
                    handler=config["handler"],
                    priority=config.get("priority", 0),
                    condition=config.get("condition"),
                    metadata=config.get("metadata"),
                )
            except Exception as e:
                self.logger.error(
                    f"导入路由规则失败: {config.get('name', 'Unknown')}, 错误: {e}"
                )

    def export_rules(self) -> List[Dict[str, Any]]:
        """
        导出路由规则配置

        Returns:
            路由规则配置列表
        """
        rules_config = []
        for route in self.routes:
            rules_config.append(
                {
                    "name": route.name,
                    "match_type": route.match_type.value,
                    "match_value": route.match_value,
                    "handler": None,  # 不导出函数对象
                    "priority": route.priority,
                    "metadata": route.metadata,
                }
            )
        return rules_config


# 工厂函数
def create_router(analyzer: Optional[MessageAnalyzer] = None) -> MessageRouter:
    """
    创建消息路由器实例

    Args:
        analyzer: 消息分析器实例

    Returns:
        MessageRouter 实例
    """
    return MessageRouter(analyzer)
