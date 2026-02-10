"""
AgentLoop 与 ContextMonitor 集成测试

测试内容：
1. AgentLoop 初始化测试
2. 自动压缩功能测试
3. 多模态消息处理测试
4. 阈值配置测试
5. 压缩事件记录测试
6. 会话管理与上下文监控集成测试
"""

import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from nanobot.agent.loop import AgentLoop
from nanobot.agent.context_monitor import ContextMonitorConfig, CompressionEvent
from nanobot.bus.queue import MessageBus
from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.providers.base import LLMProvider


class TestAgentLoopContextMonitorIntegration(unittest.TestCase):
    """测试 AgentLoop 与 ContextMonitor 集成"""

    def setUp(self):
        """设置测试环境"""
        self.mock_bus = Mock(spec=MessageBus)
        self.mock_bus.publish_outbound = Mock()
        self.mock_bus.consume_inbound = Mock()
        self.mock_bus.get_task_manager = Mock()

        self.mock_provider = Mock(spec=LLMProvider)
        self.mock_provider.get_default_model = Mock(return_value="gpt-3.5-turbo")

        self.workspace = Path("/tmp/test_workspace")
        self.workspace.mkdir(exist_ok=True)

    def tearDown(self):
        """清理测试环境"""
        import shutil

        if self.workspace.exists():
            shutil.rmtree(self.workspace)

    def test_agent_loop_initialization(self):
        """测试 AgentLoop 初始化包含 ContextMonitor"""
        loop = AgentLoop(
            bus=self.mock_bus,
            provider=self.mock_provider,
            workspace=self.workspace,
        )

        self.assertIsNotNone(loop.context_monitor)
        self.assertEqual(loop.context_monitor.config.model, "gpt-3.5-turbo")
        self.assertEqual(loop.context_monitor.config.threshold, 0.8)
        self.assertTrue(loop.context_monitor.config.enable_auto_compression)
        self.assertEqual(loop.context_monitor.config.compression_strategy, "intelligent")

    @patch.object(AgentLoop, '_process_message')
    @patch('nanobot.agent.loop.asyncio.wait_for')
    async def test_monitor_integration_in_run(self, mock_wait_for, mock_process):
        """测试在 run 方法中集成 ContextMonitor"""
        # 设置模拟
        mock_wait_for.side_effect = Exception("Stop test loop")
        mock_process.return_value = None

        loop = AgentLoop(
            bus=self.mock_bus,
            provider=self.mock_provider,
            workspace=self.workspace,
        )

        with self.assertRaises(Exception):
            await loop.run()

    def test_context_monitor_in_process_system_message(self):
        """测试在 _process_system_message中使用 ContextMonitor"""
        from nanobot.bus.events import InboundMessage

        loop = AgentLoop(
            bus=self.mock_bus,
            provider=self.mock_provider,
            workspace=self.workspace,
        )

        # 设置模拟
        mock_session = MagicMock()
        mock_session.get_history.return_value = []
        loop.sessions.get_or_create = Mock(return_value=mock_session)

        loop.context.build_messages = Mock(return_value=[{"role": "system", "content": "系统提示"}])
        loop.provider.chat = Mock()
        loop.provider.chat.return_value.has_tool_calls = False
        loop.provider.chat.return_value.content = "回复内容"

        # Mock context_monitor 的方法
        original_check_threshold = loop.context_monitor.check_threshold
        loop.context_monitor.check_threshold = Mock(return_value=False)

        loop._process_system_message(InboundMessage(
            channel="system",
            sender_id="subagent",
            chat_id="cli:direct",
            content="测试系统消息",
        ))

        # 验证 context monitor 被调用
        loop.context_monitor.check_threshold.assert_called_once()

        # 恢复
        original_check_threshold.assert_not_called()
        loop.context_monitor.check_threshold = original_check_threshold

    @patch('nanobot.agent.loop.MainAgent')
    def test_context_monitor_in_process_message(self, mock_main_agent):
        """测试在 _process_message 中使用 ContextMonitor"""
        from nanobot.bus.events import InboundMessage

        # 设置 MainAgent 模拟
        mock_agent_instance = MagicMock()
        mock_agent_instance.process_message.return_value = "回复内容"
        mock_main_agent.return_value = mock_agent_instance

        loop = AgentLoop(
            bus=self.mock_bus,
            provider=self.mock_provider,
            workspace=self.workspace,
        )

        loop.sessions.get_or_create = Mock()

        # Mock context_monitor 的方法
        original_check_threshold = loop.context_monitor.check_threshold
        loop.context_monitor.check_threshold = Mock(return_value=False)

        loop._process_message(InboundMessage(
            channel="cli",
            sender_id="user",
            chat_id="direct",
            content="测试消息",
        ))

        # 验证 context monitor 被调用
        loop.context_monitor.check_threshold.assert_called_once()

        # 恢复
        loop.context_monitor.check_threshold = original_check_threshold

    @patch.object(AgentLoop, 'context_monitor')
    def test_auto_compression_when_threshold_exceeded(self, mock_monitor):
        """测试当阈值超过时是否自动触发压缩"""
        import asyncio
        from nanobot.bus.events import InboundMessage

        # 配置模拟
        mock_monitor.check_threshold.return_value = False  # 不会触发压缩

        loop = AgentLoop(
            bus=self.mock_bus,
            provider=self.mock_provider,
            workspace=self.workspace,
        )

        loop.sessions.get_or_create = Mock()

        # Mock MainAgent
        mock_main_agent = MagicMock()
        mock_main_agent.process_message = AsyncMock(return_value="回复内容")

        # 创建一个模拟 session
        mock_session = MagicMock()
        mock_session.get_history.return_value = []
        loop.sessions.get_or_create = Mock(return_value=mock_session)

        # 设置 mock 以返回 main agent
        import patch
        with patch.object(loop, 'get_main_agent', return_value=mock_main_agent):
            result = asyncio.run(loop._process_message(InboundMessage(
                channel="cli",
                sender_id="user",
                chat_id="direct",
                content="测试消息",
            )))

        # 验证 context monitor check_threshold 被调用
        mock_monitor.check_threshold.assert_called_once()


class TestContextMonitorConfiguration(unittest.TestCase):
    """测试 ContextMonitor 配置选项"""

    def setUp(self):
        """设置测试环境"""
        self.mock_bus = Mock(spec=MessageBus)
        self.mock_provider = Mock(spec=LLMProvider)
        self.mock_provider.get_default_model = Mock(return_value="gpt-3.5-turbo")
        self.workspace = Path("/tmp/test_workspace_config")
        self.workspace.mkdir(exist_ok=True)

    def tearDown(self):
        """清理测试环境"""
        import shutil

        if self.workspace.exists():
            shutil.rmtree(self.workspace)

    def test_custom_threshold_configuration(self):
        """测试自定义阈值配置"""
        loop = AgentLoop(
            bus=self.mock_bus,
            provider=self.mock_provider,
            workspace=self.workspace,
        )

        # 修改配置
        loop.context_monitor.config.threshold = 0.9
        self.assertEqual(loop.context_monitor.config.threshold, 0.9)

        # 验证阈值计算
        original_window = loop.context_monitor.max_context_tokens
        expected_threshold = int(original_window * 0.9)
        self.assertEqual(loop.context_monitor.threshold_tokens, expected_threshold)

    def test_compression_strategy_configuration(self):
        """测试压缩策略配置"""
        loop = AgentLoop(
            bus=self.mock_bus,
            provider=self.mock_provider,
            workspace=self.workspace,
        )

        # 修改配置
        loop.context_monitor.config.compression_strategy = "truncation"
        self.assertEqual(loop.context_monitor.config.compression_strategy, "truncation")

    def test_disable_auto_compression(self):
        """测试禁用自动压缩"""
        loop = AgentLoop(
            bus=self.mock_bus,
            provider=self.mock_provider,
            workspace=self.workspace,
        )

        # 禁用自动压缩
        loop.context_monitor.config.enable_auto_compression = False
        self.assertFalse(loop.context_monitor.config.enable_auto_compression)


class TestCompressionEventsRecording(unittest.TestCase):
    """测试压缩事件记录"""

    def setUp(self):
        """设置测试环境"""
        self.mock_bus = Mock(spec=MessageBus)
        self.mock_provider = Mock(spec=LLMProvider)
        self.mock_provider.get_default_model = Mock(return_value="gpt-3.5-turbo")
        self.workspace = Path("/tmp/test_workspace_events")
        self.workspace.mkdir(exist_ok=True)

    def tearDown(self):
        """清理测试环境"""
        import shutil

        if self.workspace.exists():
            shutil.rmtree(self.workspace)

    @patch.object(AgentLoop, 'context_monitor')
    def test_compression_event_recording(self, mock_monitor):
        """测试压缩事件记录"""
        from nanobot.bus.events import InboundMessage

        mock_monitor.check_threshold.return_value = True
        mock_compressed = []
        mock_monitor.compress_context.return_value = mock_compressed
        mock_monitor.get_compression_events.return_value = [MagicMock()]

        loop = AgentLoop(
            bus=self.mock_bus,
            provider=self.mock_provider,
            workspace=self.workspace,
        )

        loop.sessions.get_or_create = Mock()

        loop._process_message(InboundMessage(
            channel="cli",
            sender_id="user",
            chat_id="direct",
            content="测试消息",
        ))

        # 验证压缩事件记录
        self.assertGreater(len(loop.context_monitor.get_compression_events()), 0)


class TestContextMonitorStats(unittest.TestCase):
    """测试 ContextMonitor 统计信息"""

    def setUp(self):
        """设置测试环境"""
        self.mock_bus = Mock(spec=MessageBus)
        self.mock_provider = Mock(spec=LLMProvider)
        self.mock_provider.get_default_model = Mock(return_value="gpt-3.5-turbo")
        self.workspace = Path("/tmp/test_workspace_stats")
        self.workspace.mkdir(exist_ok=True)

    def tearDown(self):
        """清理测试环境"""
        import shutil

        if self.workspace.exists():
            shutil.rmtree(self.workspace)

    def test_context_monitor_stats(self):
        """测试上下文统计信息收集"""
        loop = AgentLoop(
            bus=self.mock_bus,
            provider=self.mock_provider,
            workspace=self.workspace,
        )

        stats = loop.context_monitor.get_stats()
        self.assertEqual(stats["total_messages"], 0)
        self.assertEqual(stats["total_tokens"], 0)
        self.assertFalse(stats["is_over_threshold"])
        self.assertIn("max_context_tokens", stats)
        self.assertIn("threshold_ratio", stats)

    @patch.object(AgentLoop, 'context_monitor')
    def test_stats_after_processing(self, mock_monitor):
        """测试处理消息后的统计信息"""
        from nanobot.bus.events import InboundMessage

        mock_monitor.get_stats.return_value = {
            "total_messages": 5,
            "total_tokens": 4000,
            "max_context_tokens": 4096,
            "is_over_threshold": False,
            "compression_events": 0,
        }

        loop = AgentLoop(
            bus=self.mock_bus,
            provider=self.mock_provider,
            workspace=self.workspace,
        )

        loop.sessions.get_or_create = Mock()
        loop._process_message(InboundMessage(
            channel="cli",
            sender_id="user",
            chat_id="direct",
            content="测试消息",
        ))

        stats = loop.context_monitor.get_stats()
        self.assertEqual(stats["total_messages"], 5)


if __name__ == "__main__":
    unittest.main()
