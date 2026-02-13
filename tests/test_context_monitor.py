"""
ContextMonitor 单元测试

测试内容：
1. Token 计数功能测试
2. 阈值检查功能测试
3. 上下文压缩功能测试
4. 消息管理功能测试
5. 多模态消息支持测试
6. 不同模型配置测试
"""

import unittest
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from nanobot.agent.context_monitor import (
    CompressionEvent,
    ContextMonitor,
    ContextMonitorConfig,
    ModelType,
    TokenLimits,
)


class TestTokenCounting(unittest.TestCase):
    """测试 Token 计数功能"""

    def setUp(self):
        """设置测试环境"""
        self.config = ContextMonitorConfig()
        self.monitor = ContextMonitor(self.config)

    def test_empty_messages(self):
        """测试空消息列表计数"""
        self.assertEqual(self.monitor.token_count([]), 0)

    def test_simple_text_messages(self):
        """测试简单文本消息计数"""
        messages = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm fine, thank you!"},
        ]
        count = self.monitor.token_count(messages)
        self.assertGreater(count, 0)

    def test_system_message(self):
        """测试系统消息计数"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
        ]
        count = self.monitor.token_count(messages)
        self.assertGreater(count, 0)

    def test_multimodal_messages(self):
        """测试多模态消息（包含图像）计数"""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,abc123"},
                    },
                ],
            }
        ]
        count = self.monitor.token_count(messages)
        self.assertGreater(count, 0)

    def test_messages_with_tool_calls(self):
        """测试包含工具调用的消息计数"""
        messages = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "1",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": '{"path": "/test.txt"}',
                        },
                    }
                ],
            }
        ]
        count = self.monitor.token_count(messages)
        self.assertGreater(count, 0)


class TestThresholdCheck(unittest.TestCase):
    """测试阈值检查功能"""

    def setUp(self):
        """设置测试环境"""
        self.config = ContextMonitorConfig(
            model=ModelType.GPT_3_5_TURBO.value,
            threshold=0.8,
            max_tokens=100,  # 减小阈值方便测试
        )
        self.monitor = ContextMonitor(self.config)

    def test_below_threshold(self):
        """测试低于阈值的情况"""
        self.monitor.add_message({"role": "user", "content": "Hello"})
        self.assertFalse(self.monitor.check_threshold())

    @patch.object(ContextMonitor, "token_count", return_value=79)
    def test_near_threshold(self, mock_token_count):
        """测试接近阈值的情况"""
        self.assertFalse(self.monitor.check_threshold())

    @patch.object(ContextMonitor, "token_count", return_value=110)
    def test_above_threshold(self, mock_token_count):
        """测试超过阈值的情况"""
        self.assertTrue(self.monitor.check_threshold())

    @patch.object(ContextMonitor, "token_count", return_value=80)
    def test_exactly_threshold(self, mock_token_count):
        """测试正好等于阈值的情况"""
        self.assertFalse(self.monitor.check_threshold())


class TestContextCompression(unittest.TestCase):
    """测试上下文压缩功能"""

    def setUp(self):
        """设置测试环境"""
        self.config = ContextMonitorConfig(
            model=ModelType.GPT_3_5_TURBO.value,
            threshold=0.8,
            max_tokens=100,
            compression_strategy="truncation",  # 使用截断策略方便测试
        )
        self.monitor = ContextMonitor(self.config)

    def test_auto_compression_trigger(self):
        """测试自动压缩触发"""
        # 添加大量消息，确保超过阈值
        with patch.object(ContextMonitor, "token_count", side_effect=[50, 120, 90]):
            self.monitor.add_message({"role": "user", "content": "消息1"})
            self.assertTrue(len(self.monitor.get_messages()) > 0)

    @patch.object(
        ContextMonitor,
        "_truncate_context",
        return_value=[{"role": "user", "content": "压缩后的消息"}],
    )
    @patch.object(ContextMonitor, "token_count", side_effect=[150, 90])
    async def test_manual_compression(self, mock_token_count, mock_truncate):
        """测试手动压缩"""
        compressed = await self.monitor.compress_context()
        self.assertEqual(len(compressed), 1)

    @patch.object(
        ContextMonitor,
        "_truncate_context",
        return_value=[{"role": "user", "content": "压缩后的消息"}],
    )
    @patch.object(ContextMonitor, "token_count", side_effect=[150, 90])
    async def test_compression_events_recording(self, mock_token_count, mock_truncate):
        """测试压缩事件记录"""
        await self.monitor.compress_context()
        self.assertEqual(len(self.monitor.get_compression_events()), 1)

    @patch.object(ContextMonitor, "token_count", return_value=150)
    @patch.object(
        ContextMonitor,
        "_truncate_context",
        return_value=[{"role": "system", "content": "系统提示"}],
    )
    async def test_truncate_strategy(self, mock_truncate, mock_token_count):
        """测试截断策略"""
        messages = [
            {"role": "system", "content": "系统提示"},
            {"role": "user", "content": "消息1"},
            {"role": "assistant", "content": "回复1"},
            {"role": "user", "content": "消息2"},
            {"role": "assistant", "content": "回复2"},
        ]
        compressed = await self.monitor.compress_context(messages)
        self.assertEqual(len(compressed), 1)


class TestMessageManagement(unittest.TestCase):
    """测试消息管理功能"""

    def setUp(self):
        """设置测试环境"""
        self.monitor = ContextMonitor()

    def test_add_single_message(self):
        """测试添加单条消息"""
        self.monitor.add_message({"role": "user", "content": "Hello"})
        self.assertEqual(len(self.monitor.get_messages()), 1)

    def test_add_multiple_messages(self):
        """测试添加多条消息"""
        self.monitor.add_message({"role": "user", "content": "消息1"})
        self.monitor.add_message({"role": "assistant", "content": "回复1"})
        self.assertEqual(len(self.monitor.get_messages()), 2)

    def test_remove_message(self):
        """测试移除消息"""
        self.monitor.add_message({"role": "user", "content": "消息1"})
        self.monitor.add_message({"role": "assistant", "content": "回复1"})
        self.monitor.remove_message(0)
        self.assertEqual(len(self.monitor.get_messages()), 1)

    def test_remove_invalid_index(self):
        """测试移除无效索引的消息"""
        self.monitor.add_message({"role": "user", "content": "消息1"})
        with self.assertLogs(level="WARNING"):
            self.monitor.remove_message(10)
        self.assertEqual(len(self.monitor.get_messages()), 1)

    def test_clear_all_messages(self):
        """测试清空所有消息"""
        self.monitor.add_message({"role": "user", "content": "消息1"})
        self.monitor.clear()
        self.assertEqual(len(self.monitor.get_messages()), 0)


class TestModelConfiguration(unittest.TestCase):
    """测试不同模型配置"""

    def test_default_model(self):
        """测试默认模型配置"""
        monitor = ContextMonitor()
        self.assertEqual(monitor.config.model, ModelType.GPT_3_5_TURBO.value)
        self.assertGreater(monitor.max_context_tokens, 0)

    def test_custom_model(self):
        """测试自定义模型配置"""
        config = ContextMonitorConfig(model=ModelType.GPT_4.value)
        monitor = ContextMonitor(config)
        self.assertEqual(monitor.config.model, ModelType.GPT_4.value)
        # GPT-4 的上下文窗口应该更大
        self.assertGreater(
            monitor.max_context_tokens, ContextMonitor().max_context_tokens
        )

    def test_custom_max_tokens(self):
        """测试自定义最大token限制"""
        custom_max = 2000
        config = ContextMonitorConfig(max_tokens=custom_max)
        monitor = ContextMonitor(config)
        self.assertEqual(monitor.max_context_tokens, custom_max)


class TestStatsCollection(unittest.TestCase):
    """测试统计信息收集"""

    def setUp(self):
        """设置测试环境"""
        self.monitor = ContextMonitor()

    def test_initial_stats(self):
        """测试初始统计信息"""
        stats = self.monitor.get_stats()
        self.assertEqual(stats["total_messages"], 0)
        self.assertEqual(stats["total_tokens"], 0)
        self.assertFalse(stats["is_over_threshold"])

    def test_after_adding_messages(self):
        """测试添加消息后的统计信息"""
        self.monitor.add_message({"role": "user", "content": "Hello"})
        stats = self.monitor.get_stats()
        self.assertEqual(stats["total_messages"], 1)
        self.assertGreater(stats["total_tokens"], 0)


class TestIntegrationWithCompressor(unittest.TestCase):
    """测试与 ContextCompressor 的集成"""

    @patch("nanobot.agent.context_monitor.ContextCompressor")
    async def test_intelligent_compression(self, mock_compressor_class):
        """测试智能压缩策略"""
        mock_compressor = MagicMock()
        mock_compressor.compress.return_value = ("压缩后的内容", MagicMock())
        mock_compressor_class.return_value = mock_compressor

        config = ContextMonitorConfig(compression_strategy="intelligent")
        monitor = ContextMonitor(config)

        with patch.object(monitor, "token_count", side_effect=[1000, 500]):
            with patch.object(
                monitor, "_create_token_counter", return_value=lambda x: len(x) // 4
            ):
                messages = [
                    {"role": "system", "content": "系统提示"},
                    {"role": "user", "content": "长文本内容" * 100},
                ]
                compressed = await monitor.compress_context(messages)
                self.assertIn("对话历史摘要", str(compressed))


if __name__ == "__main__":
    unittest.main()
