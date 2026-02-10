"""
意图识别模块单元测试

测试三层识别器和综合识别器的功能。
"""

import pytest
import logging
from typing import Dict, Any

from nanobot.agent.intent import (
    RuleBasedRecognizer,
    MatchType,
    CodeBasedRecognizer,
    LLMRecognizer,
    LLMProvider,
    HybridRecognizer,
    RecognizerType,
    MockLLMClient
)


# 配置日志
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class TestRuleBasedRecognizer:
    """测试基于规则的识别器"""

    def test_init(self):
        """测试初始化"""
        recognizer = RuleBasedRecognizer()
        assert recognizer is not None
        assert recognizer.rule_count == 0

    def test_add_keyword_rule(self):
        """测试添加关键词规则"""
        recognizer = RuleBasedRecognizer()
        recognizer.add_keyword_rule(
            "greeting",
            "greeting",
            ["你好", "hello"]
        )
        assert recognizer.rule_count == 1

    def test_add_regex_rule(self):
        """测试添加正则表达式规则"""
        recognizer = RuleBasedRecognizer()
        recognizer.add_regex_rule(
            "phone",
            "contact.phone",
            r"\d{3}-\d{8}|\d{4}-\d{7}"
        )
        assert recognizer.rule_count == 1

    def test_recognize_keyword(self):
        """测试关键词识别"""
        recognizer = RuleBasedRecognizer()
        recognizer.add_keyword_rule(
            "greeting",
            "greeting",
            ["你好", "hello"]
        )
        result = recognizer.recognize("你好，有什么可以帮您？")
        assert result is not None
        assert result.intent == "greeting"
        assert result.rule_name == "greeting"

    def test_recognize_regex(self):
        """测试正则表达式识别"""
        recognizer = RuleBasedRecognizer()
        recognizer.add_regex_rule(
            "phone",
            "contact.phone",
            r"\d{3}-\d{8}|\d{4}-\d{7}"
        )
        result = recognizer.recognize("我的电话是：010-12345678")
        assert result is not None
        assert result.intent == "contact.phone"
        assert result.rule_name == "phone"

    def test_priority(self):
        """测试优先级规则"""
        recognizer = RuleBasedRecognizer()
        recognizer.add_keyword_rule(
            "general",
            "general.query",
            ["查询"],
            priority=1
        )
        recognizer.add_keyword_rule(
            "weather",
            "weather.query",
            ["天气"],
            priority=10
        )
        result = recognizer.recognize("今天的天气怎么样？")
        assert result is not None
        assert result.intent == "weather.query"

    def test_no_match(self):
        """测试未匹配的情况"""
        recognizer = RuleBasedRecognizer()
        result = recognizer.recognize("这是一个未匹配的文本")
        assert result is None

    def test_recognize_all(self):
        """测试识别所有匹配的结果"""
        recognizer = RuleBasedRecognizer()
        recognizer.add_keyword_rule("greeting", "greeting", ["你好"])
        recognizer.add_keyword_rule("help", "help.offer", ["帮助"])
        results = recognizer.recognize_all("你好，请帮助我")
        assert len(results) == 2
        assert any(r.intent == "greeting" for r in results)
        assert any(r.intent == "help.offer" for r in results)


class TestCodeBasedRecognizer:
    """测试基于代码逻辑的识别器"""

    def test_init(self):
        """测试初始化"""
        recognizer = CodeBasedRecognizer()
        assert recognizer is not None
        assert recognizer.rule_count == 0

    def test_add_basic_rule(self):
        """测试添加基本规则"""
        recognizer = CodeBasedRecognizer()

        def is_weather(text, context):
            return "天气" in text.lower()

        recognizer.add_rule(
            "weather",
            "weather.query",
            is_weather
        )

        assert recognizer.rule_count == 1

    def test_recognize_basic(self):
        """测试基本识别功能"""
        recognizer = CodeBasedRecognizer()

        def is_weather(text, context):
            return "天气" in text.lower()

        recognizer.add_rule(
            "weather",
            "weather.query",
            is_weather
        )

        result = recognizer.recognize("今天的天气怎么样？")
        assert result is not None
        assert result.intent == "weather.query"

    def test_add_condition_rule(self):
        """测试添加条件规则"""
        recognizer = CodeBasedRecognizer()

        def contains_weather(text, context):
            return "天气" in text.lower()

        def short_text(text, context):
            return len(text) < 50

        recognizer.add_condition_rule(
            "weather_short",
            "weather.query.short",
            [contains_weather, short_text],
            operator=all
        )

        result1 = recognizer.recognize("今天的天气怎么样？")
        assert result1 is not None
        assert result1.intent == "weather.query.short"

        result2 = recognizer.recognize("今天的天气非常好，阳光明媚，适合户外活动！" * 10)
        assert result2 is None

    def test_keyword_condition_rule(self):
        """测试关键词条件规则"""
        recognizer = CodeBasedRecognizer()
        recognizer.add_keyword_condition_rule(
            "weather",
            "weather.query",
            ["天气", "温度"]
        )
        assert recognizer.rule_count == 1

        result1 = recognizer.recognize("今天的天气怎么样？")
        assert result1 is not None
        assert result1.intent == "weather.query"

        result2 = recognizer.recognize("今天的温度很高")
        assert result2 is not None
        assert result2.intent == "weather.query"

    def test_length_rule(self):
        """测试文本长度规则"""
        recognizer = CodeBasedRecognizer()
        recognizer.add_length_rule(
            "short_text",
            "short.text",
            min_length=5,
            max_length=10
        )
        assert recognizer.rule_count == 1

        result1 = recognizer.recognize("这是一个短文本")
        assert result1 is not None
        assert result1.intent == "short.text"

        result2 = recognizer.recognize("太短")
        assert result2 is None

        result3 = recognizer.recognize("这是一个非常非常非常非常长的文本")
        assert result3 is None

    def test_context_rule(self):
        """测试上下文规则"""
        recognizer = CodeBasedRecognizer()
        recognizer.add_context_rule(
            "user_vip",
            "vip.service",
            "user_type",
            "vip"
        )
        assert recognizer.rule_count == 1

        result1 = recognizer.recognize("我需要帮助", context={"user_type": "vip"})
        assert result1 is not None
        assert result1.intent == "vip.service"

        result2 = recognizer.recognize("我需要帮助", context={"user_type": "normal"})
        assert result2 is None


class TestLLMRecognizer:
    """测试基于大模型的识别器"""

    def test_init(self):
        """测试初始化"""
        recognizer = LLMRecognizer()
        assert recognizer is not None
        assert recognizer.sample_count == 0

    def test_add_sample(self):
        """测试添加示例"""
        recognizer = LLMRecognizer()
        recognizer.add_sample("今天的天气怎么样？", "weather.query")
        assert recognizer.sample_count == 1

    def test_clear_samples(self):
        """测试清除示例"""
        recognizer = LLMRecognizer()
        recognizer.add_sample("今天的天气怎么样？", "weather.query")
        recognizer.clear_samples()
        assert recognizer.sample_count == 0

    def test_recognize_with_mock(self):
        """使用模拟客户端测试识别功能"""
        recognizer = LLMRecognizer()
        recognizer.set_client(MockLLMClient())
        result = recognizer.recognize("我想预订一张机票")
        assert result is not None
        assert isinstance(result.confidence, float)
        assert 0 <= result.confidence <= 1

    def test_recognize_batch(self):
        """测试批量识别"""
        recognizer = LLMRecognizer()
        recognizer.set_client(MockLLMClient())
        results = recognizer.recognize_batch([
            "今天的天气怎么样？",
            "我想预订机票",
            "你好"
        ])
        assert len(results) == 3
        assert all(result is not None for result in results)

    def test_custom_prompt(self):
        """测试自定义提示词"""
        recognizer = LLMRecognizer()
        custom_prompt = "你是一个专业的意图识别助手..."
        recognizer.set_prompt(custom_prompt)
        assert recognizer.get_prompt() == custom_prompt


class TestHybridRecognizer:
    """测试综合识别器"""

    def test_init(self):
        """测试初始化"""
        recognizer = HybridRecognizer()
        assert recognizer is not None
        assert recognizer.rule_recognizer.rule_count == 0
        assert recognizer.code_recognizer.rule_count == 0
        assert recognizer.llm_recognizer.sample_count == 0

    def test_recognize_rule_priority(self):
        """测试优先级机制（规则 > 代码 > LLM）"""
        recognizer = HybridRecognizer()
        recognizer.set_llm_config(LLMProvider.DOUBAO)
        recognizer.llm_recognizer.set_client(MockLLMClient())

        # 添加规则识别
        recognizer.rule_recognizer.add_keyword_rule(
            "weather",
            "weather.query",
            ["天气"]
        )

        # 添加代码识别
        def is_weather(text, context):
            return "天气" in text.lower()

        recognizer.code_recognizer.add_rule(
            "weather_code",
            "weather.query.code",
            is_weather
        )

        result = recognizer.recognize("今天的天气怎么样？")
        assert result is not None
        assert result.intent == "weather.query"
        assert result.recognizer_type == RecognizerType.RULE

    def test_fallback_strategy(self):
        """测试降级策略"""
        recognizer = HybridRecognizer()
        recognizer.set_llm_config(LLMProvider.DOUBAO)
        recognizer.llm_recognizer.set_client(MockLLMClient())

        # 没有规则匹配，应该使用 LLM
        result = recognizer.recognize("我想预订一张机票")
        assert result is not None
        assert result.recognizer_type == RecognizerType.LLM

    def test_conflict_resolution_priority(self):
        """测试冲突处理 - 优先级策略"""
        recognizer = HybridRecognizer()
        recognizer.set_llm_config(LLMProvider.DOUBAO)
        recognizer.llm_recognizer.set_client(MockLLMClient())

        # 添加规则识别（高优先级）
        recognizer.rule_recognizer.add_keyword_rule(
            "weather",
            "weather.query",
            ["天气"],
            priority=10
        )

        # 添加代码识别（低优先级）
        def is_weather(text, context):
            return "天气" in text.lower()

        recognizer.code_recognizer.add_rule(
            "weather_code",
            "weather.query.code",
            is_weather,
            priority=5
        )

        result = recognizer.recognize("今天的天气怎么样？")
        assert result is not None
        assert result.intent == "weather.query"
        assert result.recognizer_type == RecognizerType.RULE

    def test_get_all_results(self):
        """测试获取所有结果"""
        recognizer = HybridRecognizer()
        recognizer.set_llm_config(LLMProvider.DOUBAO)
        recognizer.llm_recognizer.set_client(MockLLMClient())

        # 添加规则识别
        recognizer.rule_recognizer.add_keyword_rule(
            "weather",
            "weather.query",
            ["天气"]
        )

        # 添加代码识别
        def is_weather(text, context):
            return "天气" in text.lower()

        recognizer.code_recognizer.add_rule(
            "weather_code",
            "weather.query.code",
            is_weather
        )

        results = recognizer.get_all_results("今天的天气怎么样？")
        assert len(results) >= 2
        assert any(r.recognizer_type == RecognizerType.RULE for r in results)
        assert any(r.recognizer_type == RecognizerType.CODE for r in results)


class TestIntegration:
    """集成测试"""

    def test_complete_pipeline(self):
        """测试完整的识别流程"""
        # 创建综合识别器
        recognizer = HybridRecognizer()
        recognizer.set_llm_config(LLMProvider.DOUBAO)
        recognizer.llm_recognizer.set_client(MockLLMClient())

        # 添加规则识别
        recognizer.rule_recognizer.add_keyword_rule(
            "greeting",
            "greeting",
            ["你好", "hello"],
            priority=10
        )
        recognizer.rule_recognizer.add_keyword_rule(
            "weather",
            "weather.query",
            ["天气", "温度"],
            priority=8
        )
        recognizer.rule_recognizer.add_regex_rule(
            "phone",
            "contact.phone",
            r"\d{3}-\d{8}|\d{4}-\d{7}",
            priority=5
        )

        # 添加代码识别
        def is_flight_query(text, context):
            return "机票" in text.lower() or "航班" in text.lower()

        recognizer.code_recognizer.add_rule(
            "flight",
            "flight.query",
            is_flight_query,
            confidence=0.9,
            priority=7
        )

        def is_complaint(text, context):
            words = ["投诉", "差评", "不好用", "问题", "差劲"]
            return any(word in text.lower() for word in words)

        recognizer.code_recognizer.add_rule(
            "complaint",
            "complaint",
            is_complaint,
            confidence=0.95,
            priority=9
        )

        # 添加 LLM 示例
        recognizer.llm_recognizer.add_samples([
            {
                "text": "我想预订一张从北京到上海的机票",
                "intent": "flight.query"
            },
            {
                "text": "你们的服务太差了",
                "intent": "complaint"
            }
        ])

        # 测试 1: 问候识别
        result1 = recognizer.recognize("你好，有什么可以帮您？")
        assert result1 is not None
        assert result1.intent == "greeting"
        assert result1.recognizer_type == RecognizerType.RULE

        # 测试 2: 天气查询
        result2 = recognizer.recognize("今天的温度是多少？")
        assert result2 is not None
        assert result2.intent == "weather.query"
        assert result2.recognizer_type == RecognizerType.RULE

        # 测试 3: 航班查询（代码识别）
        result3 = recognizer.recognize("我想查询明天的航班")
        assert result3 is not None
        assert result3.intent == "flight.query"
        assert result3.recognizer_type == RecognizerType.CODE

        # 测试 4: 投诉识别（代码识别）
        result4 = recognizer.recognize("你们的产品真的很差劲")
        assert result4 is not None
        assert result4.intent == "complaint"
        assert result4.recognizer_type == RecognizerType.CODE

        # 测试 5: 电话识别（正则）
        result5 = recognizer.recognize("联系电话：010-12345678")
        assert result5 is not None
        assert result5.intent == "contact.phone"
        assert result5.recognizer_type == RecognizerType.RULE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
