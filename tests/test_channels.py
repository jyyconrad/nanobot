"""
消息通道模块测试
"""

from unittest.mock import MagicMock, Mock

from nanobot.channels.base import BaseChannel
from nanobot.channels.manager import ChannelManager


def test_channel_base_class():
    """测试通道基类"""

    # 创建一个简单的通道子类，实现所有抽象方法
    class TestChannel(BaseChannel):
        async def send(self, msg):
            pass

        async def start(self):
            pass

        async def stop(self):
            pass

    # 创建模拟的 config 和 bus
    mock_config = Mock()
    mock_bus = Mock()

    channel = TestChannel(mock_config, mock_bus)
    assert channel is not None
    assert hasattr(channel, "send")
    assert hasattr(channel, "start")
    assert hasattr(channel, "stop")
    assert hasattr(channel, "is_allowed")

    print("通道基类测试通过")


def test_channel_manager():
    """测试通道管理器"""
    # 创建模拟的 config 和 bus
    mock_config = MagicMock()
    mock_bus = Mock()

    manager = ChannelManager(mock_config, mock_bus)
    assert manager is not None
    assert hasattr(manager, "get_channel")
    assert hasattr(manager, "get_status")
    assert hasattr(manager, "enabled_channels")

    print("通道管理器测试通过")


def test_channel_manager_get_channel():
    """测试获取通道"""
    # 创建模拟的 config 和 bus
    mock_config = MagicMock()
    mock_bus = Mock()

    manager = ChannelManager(mock_config, mock_bus)

    # 验证通道被正确初始化（默认配置下应该有3个通道被初始化）
    assert len(manager.enabled_channels) == 3
    assert set(manager.enabled_channels) == {"telegram", "whatsapp", "feishu"}

    # 测试 get_channel 方法
    telegram_channel = manager.get_channel("telegram")
    assert telegram_channel is not None

    whatsapp_channel = manager.get_channel("whatsapp")
    assert whatsapp_channel is not None

    feishu_channel = manager.get_channel("feishu")
    assert feishu_channel is not None

    # 测试获取不存在的通道
    assert manager.get_channel("nonexistent") is None

    print("通道获取测试通过")


def test_channel_manager_status():
    """测试通道状态"""
    # 创建模拟的 config 和 bus
    mock_config = MagicMock()
    mock_bus = Mock()

    manager = ChannelManager(mock_config, mock_bus)

    status = manager.get_status()
    assert isinstance(status, dict)

    print("通道状态测试通过")


if __name__ == "__main__":
    test_channel_base_class()
    test_channel_manager()
    test_channel_manager_get_channel()
    test_channel_manager_status()
    print("所有通道模块测试通过！")
