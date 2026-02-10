"""
消息路由器测试模块

包含 MessageRouter 和 MessageAnalyzer 的测试用例
"""

import unittest
import logging
from nanobot.agent.message_router import MessageRouter, RouteMatchType, RouteRule
from nanobot.agent.message_analyzer import MessageAnalyzer, AnalysisResult


# 配置日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestMessageAnalyzer(unittest.TestCase):
    """
    消息分析器测试类
    """

    def setUp(self):
        """
        测试前初始化
        """
        self.analyzer = MessageAnalyzer()
        logger.debug("MessageAnalyzer 测试初始化完成")

    def test_analyze_intent_greeting(self):
        """
        测试问候意图分析
        """
        text = "你好，我想咨询一些问题"
        result = self.analyzer.analyze_intent(text)
        logger.debug(f"意图分析结果: {result}")
        self.assertEqual(result["intent"], "greeting")
        self.assertGreater(result["confidence"], 0)

    def test_analyze_intent_query(self):
        """
        测试查询意图分析
        """
        text = "请问现在几点了？"
        result = self.analyzer.analyze_intent(text)
        logger.debug(f"意图分析结果: {result}")
        self.assertEqual(result["intent"], "query")
        self.assertGreater(result["confidence"], 0)

    def test_analyze_intent_command(self):
        """
        测试命令意图分析
        """
        text = "请帮我启动服务"
        result = self.analyzer.analyze_intent(text)
        logger.debug(f"意图分析结果: {result}")
        self.assertEqual(result["intent"], "command")
        self.assertGreater(result["confidence"], 0)

    def test_extract_keywords_basic(self):
        """
        测试基本关键词提取
        """
        text = "今天天气怎么样？"
        keywords = self.analyzer.extract_keywords(text)
        logger.debug(f"关键词提取结果: {keywords}")
        self.assertIn("天气", keywords)

    def test_extract_keywords_multiple(self):
        """
        测试多个关键词提取
        """
        text = "明天有什么新闻和天气信息？"
        keywords = self.analyzer.extract_keywords(text)
        logger.debug(f"关键词提取结果: {keywords}")
        self.assertIn("新闻", keywords)
        self.assertIn("天气", keywords)

    def test_detect_entities_email(self):
        """
        测试邮箱实体检测
        """
        text = "我的邮箱是test@example.com"
        entities = self.analyzer.detect_entities(text)
        logger.debug(f"实体检测结果: {entities}")
        self.assertIn("email", entities)
        self.assertIn("test@example.com", entities["email"])

    def test_detect_entities_phone(self):
        """
        测试电话实体检测
        """
        text = "联系电话是13812345678"
        entities = self.analyzer.detect_entities(text)
        logger.debug(f"实体检测结果: {entities}")
        self.assertIn("phone", entities)
        self.assertIn("13812345678", entities["phone"])

    def test_detect_entities_datetime(self):
        """
        测试日期时间实体检测
        """
        text = "会议时间是2025年12月25日下午3点"
        entities = self.analyzer.detect_entities(text)
        logger.debug(f"实体检测结果: {entities}")
        self.assertIn("datetime", entities)
        self.assertNotEqual(entities["datetime"], [])

    def test_complete_analysis(self):
        """
        测试完整分析
        """
        text = "你好，请问明天的天气怎么样？"
        result = self.analyzer.analyze(text)
        logger.debug(f"完整分析结果: {result}")

        self.assertEqual(result.intent, "greeting")
        self.assertIn("天气", result.keywords)
        self.assertGreater(result.confidence, 0)


class TestMessageRouter(unittest.TestCase):
    """
    消息路由器测试类
    """

    def setUp(self):
        """
        测试前初始化
        """
        self.analyzer = MessageAnalyzer()
        self.router = MessageRouter(self.analyzer)
        self.test_counter = 0
        logger.debug("MessageRouter 测试初始化完成")

    def test_register_handler(self):
        """
        测试注册处理器
        """
        def test_handler(data):
            self.test_counter += 1
            return f"处理: {data['message']['text']}"

        self.router.register_handler("test_handler", test_handler)
        self.assertIn("test_handler", self.router.get_handlers())

    def test_unregister_handler(self):
        """
        测试注销处理器
        """
        def test_handler(data):
            pass

        self.router.register_handler("test_handler", test_handler)
        removed = self.router.unregister_handler("test_handler")
        self.assertIsNotNone(removed)
        self.assertNotIn("test_handler", self.router.get_handlers())

    def test_add_and_remove_route(self):
        """
        测试添加和移除路由规则
        """
        def test_handler(data):
            pass

        rule = RouteRule(
            name="test_route",
            match_type=RouteMatchType.EXACT,
            match_value="test",
            handler=test_handler,
            priority=1
        )

        self.router.add_route(rule)
        self.assertEqual(len(self.router.get_routes()), 1)

        removed = self.router.remove_route("test_route")
        self.assertIsNotNone(removed)
        self.assertEqual(len(self.router.get_routes()), 0)

    def test_route_exact_match(self):
        """
        测试精确匹配路由
        """
        def greeting_handler(data):
            return "问候处理"

        def query_handler(data):
            return "查询处理"

        self.router.register_handler("greeting", greeting_handler)
        self.router.register_handler("query", query_handler)

        self.router.create_route(
            name="greeting_route",
            match_type=RouteMatchType.EXACT,
            match_value="你好",
            handler="greeting",
            priority=1
        )

        result = self.router.route_message({"text": "你好"})
        logger.debug(f"路由结果: {result}")
        self.assertEqual(result, "问候处理")

    def test_route_intent_match(self):
        """
        测试意图匹配路由
        """
        def query_handler(data):
            return "查询处理"

        self.router.register_handler("query", query_handler)

        self.router.create_route(
            name="query_route",
            match_type=RouteMatchType.INTENT,
            match_value="query",
            handler="query",
            priority=1
        )

        result = self.router.route_message({"text": "请问现在几点了？"})
        logger.debug(f"路由结果: {result}")
        self.assertEqual(result, "查询处理")

    def test_route_keyword_match(self):
        """
        测试关键词匹配路由
        """
        def weather_handler(data):
            return "天气处理"

        self.router.register_handler("weather", weather_handler)

        self.router.create_route(
            name="weather_route",
            match_type=RouteMatchType.KEYWORD,
            match_value="天气",
            handler="weather",
            priority=1
        )

        result = self.router.route_message({"text": "今天天气怎么样？"})
        logger.debug(f"路由结果: {result}")
        self.assertEqual(result, "天气处理")

    def test_route_priority(self):
        """
        测试路由优先级
        """
        def high_priority_handler(data):
            return "高优先级处理"

        def low_priority_handler(data):
            return "低优先级处理"

        self.router.register_handler("high", high_priority_handler)
        self.router.register_handler("low", low_priority_handler)

        self.router.create_route(
            name="high_route",
            match_type=RouteMatchType.CONTAINS,
            match_value="测试",
            handler="high",
            priority=10
        )

        self.router.create_route(
            name="low_route",
            match_type=RouteMatchType.CONTAINS,
            match_value="测试",
            handler="low",
            priority=1
        )

        result = self.router.route_message({"text": "这是一个测试消息"})
        logger.debug(f"路由结果: {result}")
        self.assertEqual(result, "高优先级处理")

    def test_default_handler(self):
        """
        测试默认处理器
        """
        def default_handler(data):
            return "默认处理"

        self.router.set_default_handler(default_handler)

        result = self.router.route_message({"text": "未知消息类型"})
        logger.debug(f"默认处理结果: {result}")
        self.assertEqual(result, "默认处理")


if __name__ == '__main__':
    logger.info("开始运行消息路由器测试")
    unittest.main()
