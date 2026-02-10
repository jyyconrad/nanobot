"""
消息分析器模块 - 负责分析消息意图、提取关键词和检测实体

该模块提供了 MessageAnalyzer 类，用于对文本消息进行深入分析，
包括意图识别、关键词提取和实体检测功能，为消息路由提供基础支持。
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field

# 配置日志记录
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


@dataclass
class AnalysisResult:
    """
    消息分析结果数据类

    包含消息的意图分析、关键词提取和实体检测结果
    """
    intent: str
    confidence: float
    keywords: List[str]
    entities: Dict[str, Any]
    raw_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class MessageAnalyzer:
    """
    消息分析器类

    提供消息意图分析、关键词提取和实体检测功能，
    支持基于规则和模式的分析方法。
    """

    def __init__(self):
        """
        初始化消息分析器

        设置预定义的意图模式和关键词库
        """
        self.logger = logger
        self.intent_patterns: Dict[str, List[re.Pattern]] = {
            "greeting": [
                re.compile(r"^(你好|您好|哈喽|嗨|早|早上好|晚上好|下午好)", re.IGNORECASE),
                re.compile(r"^.*(问候|打招呼).*$", re.IGNORECASE)
            ],
            "query": [
                re.compile(r"^.*(查询|查找|搜索|问|请问|想知道|了解).*$", re.IGNORECASE),
                re.compile(r"^.*(\?|\？)$")
            ],
            "command": [
                re.compile(r"^.*(执行|运行|启动|停止|暂停|继续|打开|关闭).*$", re.IGNORECASE),
                re.compile(r"^.*(命令|操作|控制).*$", re.IGNORECASE)
            ],
            "request": [
                re.compile(r"^.*(需要|请求|要求|希望|想要|请).*$", re.IGNORECASE),
                re.compile(r"^.*(帮忙|协助|支持).*$", re.IGNORECASE)
            ],
            "feedback": [
                re.compile(r"^.*(反馈|建议|意见|评价|评论|吐槽).*$", re.IGNORECASE),
                re.compile(r"^.*(好|不好|满意|不满意|喜欢|不喜欢).*$", re.IGNORECASE)
            ],
            "unknown": []
        }

        self.keyword_patterns: Dict[str, List[str]] = {
            "time": ["时间", "现在几点", "时钟", "时刻"],
            "weather": ["天气", "气温", "温度", "预报", "下雨", "下雪", "晴天"],
            "news": ["新闻", "资讯", "消息", "头条"],
            "calendar": ["日历", "日程", "约会", "提醒", "事件"],
            "email": ["邮件", "邮箱", "发送邮件", "收件箱"],
            "search": ["搜索", "查找", "查询", "搜索一下"]
        }

        self.entity_patterns: Dict[str, re.Pattern] = {
            "datetime": re.compile(
                r"(\d{4}年)?(\d{1,2}月)?(\d{1,2}日)?"
                r"(\d{1,2}时)?(\d{1,2}分)?(\d{1,2}秒)?",
                re.IGNORECASE
            ),
            "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
            "phone": re.compile(r"1[3-9]\d{9}"),
            "url": re.compile(r"https?://[^\s]+"),
            "number": re.compile(r"\d+(\.\d+)?")
        }

        self.stop_words: Set[str] = {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
            "一个", "上", "也", "很", "到", "说", "去", "你", "会", "着", "没有",
            "看", "好", "自己", "这", "那", "里", "来", "他们", "出", "还", "你的",
            "们", "现在", "起", "点", "中", "后", "看", "所", "以"
        }

    def analyze_intent(self, text: str) -> Dict[str, float]:
        """
        分析消息意图

        根据预定义的意图模式匹配文本，返回意图及其置信度

        Args:
            text: 要分析的文本消息

        Returns:
            包含意图和置信度的字典，格式: {"intent": "意图名称", "confidence": 置信度}
        """
        self.logger.debug(f"分析意图: {text}")

        best_intent = "unknown"
        best_confidence = 0.0

        for intent, patterns in self.intent_patterns.items():
            if intent == "unknown":
                continue

            matched_patterns = 0
            total_patterns = len(patterns)

            for pattern in patterns:
                if pattern.search(text):
                    matched_patterns += 1

            if total_patterns > 0:
                confidence = matched_patterns / total_patterns

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_intent = intent

        self.logger.debug(f"意图分析结果: {best_intent}, 置信度: {best_confidence:.2f}")
        return {"intent": best_intent, "confidence": best_confidence}

    def extract_keywords(self, text: str) -> List[str]:
        """
        提取消息关键词

        根据预定义的关键词库和文本模式提取关键词

        Args:
            text: 要分析的文本消息

        Returns:
            关键词列表
        """
        self.logger.debug(f"提取关键词: {text}")

        keywords: List[str] = []

        # 基于预定义关键词库提取
        for category, terms in self.keyword_patterns.items():
            for term in terms:
                if term in text:
                    keywords.append(term)

        # 基于模式匹配提取
        word_pattern = re.compile(r"[\u4e00-\u9fff]+")
        words = word_pattern.findall(text)

        # 过滤停用词和短词
        filtered_words = [
            word for word in words
            if len(word) > 1 and word not in self.stop_words and word not in keywords
        ]

        # 添加过滤后的词
        keywords.extend(filtered_words)

        # 去重
        unique_keywords = []
        seen = set()
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)

        self.logger.debug(f"关键词提取结果: {unique_keywords}")
        return unique_keywords

    def detect_entities(self, text: str) -> Dict[str, Any]:
        """
        检测消息中的实体

        使用正则表达式模式检测文本中的各种实体类型

        Args:
            text: 要分析的文本消息

        Returns:
            包含实体信息的字典，键为实体类型，值为检测到的实体列表
        """
        self.logger.debug(f"检测实体: {text}")

        entities: Dict[str, Any] = {}

        for entity_type, pattern in self.entity_patterns.items():
            matches = pattern.findall(text)
            if matches:
                # 处理不同实体类型的匹配结果
                if entity_type == "datetime":
                    # 合并日期时间匹配
                    datetime_str = ""
                    for match in matches:
                        merged = "".join([part for part in match if part])
                        if merged:
                            if datetime_str:
                                datetime_str += " "
                            datetime_str += merged
                    entities[entity_type] = datetime_str if datetime_str else []
                else:
                    # 其他实体类型直接保存匹配结果
                    unique_matches = list(set(matches))
                    entities[entity_type] = unique_matches

        self.logger.debug(f"实体检测结果: {entities}")
        return entities

    def analyze(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """
        完整分析消息

        执行完整的消息分析流程，包括意图分析、关键词提取和实体检测

        Args:
            text: 要分析的文本消息
            metadata: 附加的元数据信息

        Returns:
            包含所有分析结果的 AnalysisResult 对象
        """
        self.logger.debug(f"完整分析消息: {text}")

        # 执行各个分析步骤
        intent_result = self.analyze_intent(text)
        keywords = self.extract_keywords(text)
        entities = self.detect_entities(text)

        # 合并结果
        result = AnalysisResult(
            intent=intent_result["intent"],
            confidence=intent_result["confidence"],
            keywords=keywords,
            entities=entities,
            raw_text=text,
            metadata=metadata or {}
        )

        self.logger.info(f"消息分析完成: {result}")
        return result

    def add_intent_pattern(self, intent: str, pattern: str, case_sensitive: bool = False):
        """
        添加新的意图模式

        Args:
            intent: 意图名称
            pattern: 正则表达式模式字符串
            case_sensitive: 是否区分大小写，默认为 False
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        compiled_pattern = re.compile(pattern, flags)

        if intent not in self.intent_patterns:
            self.intent_patterns[intent] = []

        self.intent_patterns[intent].append(compiled_pattern)
        self.logger.debug(f"添加意图模式: {intent} - {pattern}")

    def add_keyword_category(self, category: str, keywords: List[str]):
        """
        添加新的关键词类别

        Args:
            category: 关键词类别名称
            keywords: 关键词列表
        """
        if category not in self.keyword_patterns:
            self.keyword_patterns[category] = []

        self.keyword_patterns[category].extend(keywords)
        self.logger.debug(f"添加关键词类别: {category} - {keywords}")

    def add_entity_pattern(self, entity_type: str, pattern: str, case_sensitive: bool = False):
        """
        添加新的实体检测模式

        Args:
            entity_type: 实体类型名称
            pattern: 正则表达式模式字符串
            case_sensitive: 是否区分大小写，默认为 False
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        compiled_pattern = re.compile(pattern, flags)
        self.entity_patterns[entity_type] = compiled_pattern
        self.logger.debug(f"添加实体模式: {entity_type} - {pattern}")

    def add_stop_words(self, words: List[str]):
        """
        添加停用词

        Args:
            words: 停用词列表
        """
        self.stop_words.update(words)
        self.logger.debug(f"添加停用词: {words}")
